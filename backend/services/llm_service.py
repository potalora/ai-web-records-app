import os
import asyncio
import mimetypes
from typing import List, Dict, Literal, Tuple, Optional
from fastapi import UploadFile
import base64
import logging
import io
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
from pdf2image import convert_from_bytes

from openai import OpenAI, AsyncOpenAI, APIError as OpenAIAPIError
import google.generativeai as genai
from google.api_core import exceptions as GoogleAPIErrors
from anthropic import AsyncAnthropic, APIError as AnthropicAPIError

# Import constants
from backend.core import constants

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Environment Setup & Clients ---

# Load API keys from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Initialize clients
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
anthropic_client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

# Configure Google client (synchronous for model listing)
try:
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
    else:
        logging.warning("Google API Key not found. Google models will not be available.")
        genai = None # Disable Google features if key is missing
except Exception as e:
    logging.error(f"Failed to configure Google GenAI client: {e}")
    genai = None

# --- Defaults & Helper Functions ---

# Use defaults from constants
DEFAULT_OPENAI_MODEL = constants.DEFAULT_OPENAI_MODEL
DEFAULT_GOOGLE_MODEL = constants.DEFAULT_GOOGLE_MODEL
DEFAULT_ANTHROPIC_MODEL = constants.DEFAULT_ANTHROPIC_MODEL

def get_mime_type(filename):
    """Gets the MIME type of a file based on its extension."""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream' # Default if type unknown

logger = logging.getLogger(__name__)

# === Helper Functions ===

# Heuristic: Consider PDF image-based if average characters per page is low
TEXT_EXTRACTION_THRESHOLD_PER_PAGE = 500

def analyze_pdf_content(pdf_content: bytes) -> Tuple[str, Optional[str]]:
    """Analyzes PDF content to extract text and determine if it's image-based.

    Args:
        pdf_content: The byte content of the PDF file.

    Returns:
        A tuple containing:
        - pdf_type: 'text' or 'image'.
        - extracted_text: The extracted text if pdf_type is 'text', otherwise None.
    """
    extracted_text = ""
    pdf_type = 'image'  # Default to image
    try:
        pdf_file = io.BytesIO(pdf_content)
        reader = PdfReader(pdf_file)
        num_pages = len(reader.pages)
        if num_pages == 0:
            logger.warning("PDF has 0 pages.")
            return 'image', None # Treat as image if no pages

        total_chars = 0
        for page in reader.pages:
            try:
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n\n" # Add separator
                    total_chars += len(page_text)
            except Exception as page_error:
                logger.warning(f"Error extracting text from a page: {page_error}")
                continue # Try next page

        avg_chars_per_page = total_chars / num_pages if num_pages > 0 else 0
        logger.info(f"PDF Analysis: {num_pages} pages, {total_chars} total chars, {avg_chars_per_page:.2f} avg chars/page.")

        if avg_chars_per_page >= TEXT_EXTRACTION_THRESHOLD_PER_PAGE:
            pdf_type = 'text'
            logger.info("Classified PDF as text-based.")
            return pdf_type, extracted_text.strip()
        else:
            logger.info("Classified PDF as image-based (low text content).")
            return 'image', None

    except PdfReadError as e:
        logger.error(f"PyPDF2 error reading PDF: {e}")
        # Could be encrypted, corrupted, or truly image-based
        return 'image', None
    except Exception as e:
        logger.error(f"Unexpected error analyzing PDF content: {e}", exc_info=True)
        return 'image', None # Fallback to image if analysis fails

def convert_pdf_to_images(pdf_content: bytes) -> List[str]:
    """Converts PDF pages to a list of base64 encoded PNG images."""
    base64_images = []
    try:
        # Convert PDF bytes to PIL Image objects at 300 DPI
        images = convert_from_bytes(pdf_content, fmt='png', dpi=300)
        
        for i, img in enumerate(images):
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            base64_images.append(img_str)
            logger.debug(f"Encoded page {i+1} to base64 string.")

        return base64_images

    except Exception as e:
        # This could be due to various issues: poppler not found, corrupted PDF,
        # memory errors for large PDFs, etc.
        logger.error(f"Error converting PDF to images: {e}", exc_info=True)
        return [] # Return empty list on failure

# --- Model Listing Functions ---

async def _fetch_dynamic_openai_models() -> List[Dict[str, str]]:
    """Fetches available models from the OpenAI API."""
    openai_models = []
    if not OPENAI_API_KEY:
        logging.warning("OpenAI API Key not found. Skipping OpenAI model fetch.")
        return []
    try:
        logging.info("Fetching available models from OpenAI API...")
        response_page = await openai_client.models.list() # Await the async call
        all_listed_models = response_page.data if response_page.data else []

        # Filter for models suitable for PDF summarization / vision
        suitable_ids = {'gpt-4o', 'gpt-4-turbo', 'gpt-4o-mini'} # Add others if needed

        for model in all_listed_models:
            if model.id in suitable_ids: # Basic filtering by known suitable IDs
                 # We could add more sophisticated filtering based on model capabilities if the API provided it
                 openai_models.append({
                    "id": model.id,
                    "provider": "openai",
                    "name": model.id # Often, OpenAI ID is the display name
                })
        logging.info(f"Found {len(openai_models)} suitable OpenAI models.")
    except OpenAIAPIError as e:
        logging.error(f"OpenAI API error listing models: {e}")
    except Exception as e:
        logging.error(f"Unexpected error fetching OpenAI models: {e}")
    return openai_models

def _fetch_dynamic_google_models() -> List[Dict[str, str]]:
    """Fetches available models from the Google Generative AI API."""
    google_models = []
    if not genai:
        logging.warning("Google client not configured, skipping Google model fetch.")
        return []
    try:
        logging.info("Fetching available models from Google API...")
        for m in genai.list_models():
            # Reverted: Filter for models supporting 'generateContent' (text/vision)
            # And specifically models that seem suitable for summarization/vision (basic 'gemini' check)
            # This filtering logic might need refinement based on future models/API changes
            if 'generateContent' in m.supported_generation_methods:
                # Simple check: include 'gemini' models
                if 'gemini' in m.name:
                    model_id = m.name.split('/')[-1] # Extract short ID like 'gemini-1.5-pro-latest'
                    model_name = getattr(m, 'display_name', m.name) # Use display_name or name
                    google_models.append({
                        "id": model_id,
                        "provider": "google",
                        "name": model_name # Use display_name if available, otherwise fall back to name
                    })
        logging.info(f"Found {len(google_models)} suitable Google models.")
    except GoogleAPIErrors.PermissionDenied:
        logging.error("Google API key is invalid or lacks permissions to list models.")
    except Exception as e:
        logging.error(f"Failed to fetch Google models: {e}")
    return google_models

async def get_anthropic_pdf_models() -> List[str]:
    """Returns a hardcoded list of known Anthropic models supporting PDF uploads."""
    known_anthropic_models = constants.KNOWN_ANTHROPIC_PDF_MODELS
    logging.info(f"Using hardcoded Anthropic PDF-capable models: {known_anthropic_models}")
    return known_anthropic_models

async def get_available_pdf_models() -> Dict[str, List[Dict[str, str]]]:
    """Gets available models suitable for PDF summarization from configured providers."""
    # Fetch dynamically where implemented
    google_models = _fetch_dynamic_google_models()
    # Await the async function call
    openai_models = await _fetch_dynamic_openai_models()
 
    # Get static lists for other providers and format them
    anthropic_models_raw = getattr(constants, 'KNOWN_ANTHROPIC_PDF_MODELS', [])
 
    anthropic_models = [
        {"id": model_id, "provider": "anthropic", "name": model_id}
        for model_id in anthropic_models_raw
    ]

    # Combine models
    all_models = {
        "openai": openai_models,
        "google": google_models, # Use dynamic list
        "anthropic": anthropic_models,
    }

    # Filter based on suitability (optional, could be done in fetch functions)
    # For now, assume fetch functions return suitable models
    pdf_suitable_models = {
        provider: models
        for provider, models in all_models.items()
        if models # Only include providers with available models
    }
    return pdf_suitable_models

# --- Summarization Functions ---

SUMMARIZATION_PROMPT = "Summarize the following medical record content, focusing on key diagnoses, treatments, medications, and allergies:"
IMAGE_SUMMARIZATION_PROMPT = "Analyze the following medical document page image(s) and provide a concise summary, focusing on key diagnoses, treatments, medications, and allergies mentioned or depicted."

async def summarize_pdf_openai(
    model_id: str,
    text_content: Optional[str] = None,
    image_data: Optional[List[str]] = None
) -> str:
    """Summarizes PDF content (text or images) using the OpenAI API."""
    if not text_content and not image_data:
        raise ValueError("Either text_content or image_data must be provided.")
    if text_content and image_data:
         raise ValueError("Provide either text_content or image_data, not both.")

    logger.info(f"Summarizing with OpenAI model: {model_id}")
    messages = []
    if text_content:
        logger.debug("Building OpenAI request for text content.")
        messages = [
            {"role": "system", "content": "You are a helpful medical assistant specializing in summarizing records."},
            {"role": "user", "content": f"{SUMMARIZATION_PROMPT}\n\n{text_content}"}
        ]
    elif image_data:
        logger.debug(f"Building OpenAI request for {len(image_data)} image(s).")
        # Construct messages for OpenAI API (multi-modal)
        messages = [
            {"role": "user", "content": [
                {"type": "text", "text": IMAGE_SUMMARIZATION_PROMPT},
                *[
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/png;base64,{img_b64}"
                    }}
                    for img_b64 in image_data
                ]
            ]}
        ]

    try:
        response = await openai_client.chat.completions.create(
            model=model_id,
            messages=messages,
            max_tokens=1024 # Adjust as needed
        )
        summary = response.choices[0].message.content
        logger.info(f"Successfully received summary from OpenAI model {model_id}.")
        return summary.strip() if summary else ""
    except OpenAIAPIError as e:
        logging.error(f"OpenAI API Error using model {model_id}: Status={e.status_code}, Message={e.message}", exc_info=True)
        # Consider extracting more details if available in e.body or e.response
        raise # Re-raise the original error for main.py to handle
    except Exception as e:
        logging.error(f"Error during OpenAI summarization using model {model_id}: {e}", exc_info=True)
        raise

async def summarize_pdf_google(
    model_id: str,
    text_content: Optional[str] = None,
    image_data: Optional[List[str]] = None
) -> str:
    """Summarizes PDF content (text or images) using the Google Gemini API."""
    if not text_content and not image_data:
        raise ValueError("Either text_content or image_data must be provided.")
    if text_content and image_data:
         raise ValueError("Provide either text_content or image_data, not both.")

    logger.info(f"Summarizing with Google model: {model_id}")
    # Prepare parts for Google API (multi-modal)
    parts = []
    if text_content:
        logger.debug("Building Google request for text content.")
        parts.append(SUMMARIZATION_PROMPT)
        parts.append("\n\n")
        parts.append(text_content)
    elif image_data:
        logger.debug(f"Building Google request for {len(image_data)} image(s).")
        parts.append(IMAGE_SUMMARIZATION_PROMPT)
        for i, img_b64 in enumerate(image_data):
            # Gemini expects image parts directly from bytes
            img_bytes = base64.b64decode(img_b64)
            image_part = {
                "mime_type": "image/png",
                "data": img_bytes
            }
            parts.append(image_part)
            logger.debug(f"Added image {i+1} to Google request.")

    logger.info(f"Sending request to Google model {model_id}...")
    # Note: Gemini API calls are synchronous in the current library version
    # We might run this in a threadpool executor for true async behavior if needed
    response = await asyncio.to_thread(genai.GenerativeModel(model_id).generate_content, parts)

    summary = response.text
    logger.info(f"Successfully received summary from Google model {model_id}.")
    return summary.strip() if summary else ""

async def summarize_pdf_anthropic(
    model_id: str,
    text_content: Optional[str] = None,
    image_data: Optional[List[str]] = None
) -> str:
    """Summarizes PDF content (text or images) using the Anthropic Claude API."""
    # Implementation pending adaptation
    if not text_content and not image_data:
        raise ValueError("Either text_content or image_data must be provided for Anthropic.")
    if text_content and image_data:
         raise ValueError("Provide either text_content or image_data for Anthropic, not both.")

    logger.info(f"Summarizing with Anthropic model: {model_id}")
    target_model = model_id # Use the provided model_id directly

    try:
        # Prepare messages for Anthropic API (multi-modal)
        messages = []
        if text_content:
            messages = [
                {"role": "user", "content": f"{SUMMARIZATION_PROMPT}\n\n{text_content}"}
            ]
        elif image_data:
            # Claude Vision API message structure
            content_blocks = [{"type": "text", "text": IMAGE_SUMMARIZATION_PROMPT}]
            for img_b64 in image_data:
                 content_blocks.append({
                     "type": "image",
                     "source": {
                         "type": "base64",
                         "media_type": "image/png",
                         "data": img_b64
                     }
                 })
            messages = [
                {"role": "user", "content": content_blocks}
            ]

        logger.info(f"Sending request to Anthropic model {target_model}...")
        response = await anthropic_client.messages.create(
            model=target_model,
            max_tokens=1024,
            messages=messages
        )
        summary = ""
        if response.content and isinstance(response.content, list):
            # Find the first text block in the response
            for block in response.content:
                if hasattr(block, 'text'):
                    summary = block.text
                    break

        logger.info(f"Successfully received summary from Anthropic model {target_model}.")
        return summary.strip() if summary else ""
    except AnthropicAPIError as e:
        logging.error(f"Anthropic API Error using model {target_model}: Status={e.status_code}, Message={e.message}", exc_info=True)
        raise
    except Exception as e:
        logging.error(f"Error during Anthropic summarization using model {target_model}: {e}", exc_info=True)
        raise


# --- Main Router Function ---

async def summarize_pdf_auto(provider: Literal['openai', 'google', 'anthropic'], model_id: str, pdf_file: UploadFile) -> str:
    """Summarizes a PDF using the specified provider and model, automatically handling text vs. image PDFs."""
    logger.info(f"Starting PDF summarization with {provider=}, {model_id=}, filename='{pdf_file.filename}'.")
    try:
        pdf_content = await pdf_file.read()
        if not pdf_content:
            logger.error("Uploaded PDF file is empty.")
            raise HTTPException(status_code=400, detail="Uploaded PDF file is empty.")

        logger.info("Analyzing PDF content...")
        pdf_type, extracted_text = analyze_pdf_content(pdf_content)

        summary = ""
        if pdf_type == 'text' and extracted_text:
            logger.info(f"Processing PDF as text. Extracted {len(extracted_text)} characters.")
            if provider == 'openai':
                # TODO: Update summarize_pdf_openai to accept text_content
                summary = await summarize_pdf_openai(model_id, text_content=extracted_text)
            elif provider == 'google':
                # TODO: Update summarize_pdf_google to accept text_content
                summary = await summarize_pdf_google(model_id, text_content=extracted_text)
            elif provider == 'anthropic':
                # TODO: Update summarize_pdf_anthropic to accept text_content
                summary = await summarize_pdf_anthropic(model_id, text_content=extracted_text)
        elif pdf_type == 'image':
            logger.info("Processing PDF as image. Converting pages...")
            base64_images = convert_pdf_to_images(pdf_content)
            if not base64_images:
                logger.error("Failed to convert PDF to images.")
                raise HTTPException(status_code=500, detail="Failed to convert PDF to images. The file might be corrupted or require a password.")

            logger.info(f"Successfully converted PDF to {len(base64_images)} images. Sending to provider...")
            if provider == 'openai':
                 # TODO: Update summarize_pdf_openai to accept image_data
                summary = await summarize_pdf_openai(model_id, image_data=base64_images)
            elif provider == 'google':
                 # TODO: Update summarize_pdf_google to accept image_data
                summary = await summarize_pdf_google(model_id, image_data=base64_images)
            elif provider == 'anthropic':
                 # TODO: Update summarize_pdf_anthropic to accept image_data
                summary = await summarize_pdf_anthropic(model_id, image_data=base64_images)
        else:
             # Should not happen if analyze_pdf_content is correct
             logger.error(f"Unexpected pdf_type '{pdf_type}' from analyze_pdf_content.")
             raise HTTPException(status_code=500, detail="Internal server error during PDF analysis.")

        logger.info(f"Successfully generated summary using {provider} model {model_id}.")
        return summary

    except HTTPException as http_exc:
        logger.error(f"HTTP Exception during PDF summarization: {http_exc}")
        raise
    except Exception as e:
        logger.error(f"Error during PDF summarization: {e}", exc_info=True)
        raise
