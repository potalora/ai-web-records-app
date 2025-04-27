import os
import asyncio
from typing import List, Literal, Optional, Any
from fastapi import UploadFile, HTTPException
import base64
import logging
from PIL import Image
import io

# Import API clients
from openai import AsyncOpenAI, OpenAIError
from anthropic import AsyncAnthropic, AnthropicError
import google.generativeai as genai

# PDF processing
from PyPDF2 import PdfReader
import fitz  # PyMuPDF

# Configure basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Environment Setup & Lazy Client Initialization ---

# Global variables to hold client instances (initialized lazily)
_openai_client: Optional[AsyncOpenAI] = None
_anthropic_client: Optional[AsyncAnthropic] = None
_google_configured: bool = False  # Flag to track if genai.configure was called


def _get_openai_client() -> AsyncOpenAI:
    """Lazily initializes and returns the AsyncOpenAI client."""
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable not set.")
            raise OpenAIError("OpenAI API key not configured.")
        try:
            _openai_client = AsyncOpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}", exc_info=True)
            raise OpenAIError(f"Failed to initialize OpenAI client: {e}")
    return _openai_client


def _get_anthropic_client() -> AsyncAnthropic:
    """Lazily initializes and returns the AsyncAnthropic client."""
    global _anthropic_client
    if _anthropic_client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY environment variable not set.")
            raise AnthropicError("Anthropic API key not configured.")
        try:
            _anthropic_client = AsyncAnthropic(api_key=api_key)
            logger.info("Anthropic client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}", exc_info=True)
            raise AnthropicError(f"Failed to initialize Anthropic client: {e}")
    return _anthropic_client


def _configure_google_genai():
    """Lazily configures the Google GenAI library."""
    global _google_configured
    if not _google_configured:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY not set. Google models will be unavailable.")
            # We don't raise an error here, just disable Google functionality
            # Mark as configured to avoid repeated checks/warnings
            _google_configured = True
            return False  # Indicate configuration failed due to missing key
        try:
            genai.configure(api_key=api_key)
            _google_configured = True
            logger.info("Google GenAI client configured successfully.")
            return True  # Indicate success
        except Exception as e:
            logger.error(f"Failed to configure Google GenAI client: {e}", exc_info=True)
            # Mark as configured to avoid repeated attempts on error
            _google_configured = True
            return False  # Indicate configuration failed
    # Return True if already configured successfully, False otherwise
    return genai is not None and _google_configured and bool(os.getenv("GOOGLE_API_KEY"))


def _get_google_client(model_id: str) -> Optional[genai.GenerativeModel]:
    """Configures Google GenAI if needed and returns a GenerativeModel instance."""
    if not _configure_google_genai():  # Attempt configuration if not done yet
        logger.warning(f"Google GenAI not configured or key missing. Cannot get model '{model_id}'.")
        return None  # Return None if configuration failed or key is missing
    try:
        model = genai.GenerativeModel(model_id)
        return model
    except Exception as e:
        logger.error(f"Failed to get Google GenerativeModel '{model_id}': {e}", exc_info=True)
        return None


# --- PDF Content Extraction --- #

async def extract_text_from_pdf(file_content: bytes) -> str:
    """Extracts text content from a PDF file."""
    # ... (rest of function remains the same)
    pass


async def extract_images_from_pdf(file_content: bytes) -> List[str]:
    """Extracts images from each page of a PDF and returns them as base64 encoded strings."""
    # ... (rest of function remains the same)
    pass


# --- Provider-Specific Summarization Functions --- #

async def summarize_pdf_openai(
    model_id: str,
    text_content: Optional[str] = None,
    image_data: Optional[List[str]] = None,
) -> str:
    """Summarizes PDF content (text or images) using the OpenAI API."""
    client = _get_openai_client()  # Use getter
    messages = [
        {
            "role": "system",
            "content": "You are an expert medical assistant. Summarize the provided medical document content accurately and concisely.",
        }
    ]
    # ... (rest of function needs to use 'client' instead of 'openai_client')
    content_list = []
    if text_content:
        content_list.append({"type": "text", "text": text_content})
        logger.info(f"Preparing OpenAI request with text content ({len(text_content)} chars).")

    if image_data:
        for i, img_b64 in enumerate(image_data):
            # Ensure the base64 string has the correct prefix if necessary
            # Assuming img_b64 is the raw base64 data
            content_list.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_b64}",  # Assuming PNG, adjust if needed
                        "detail": "low",  # Use low detail for summarization to save tokens
                    },
                }
            )
        logger.info(f"Preparing OpenAI request with {len(image_data)} images.")

    if not content_list:
        logger.warning("No text or image content provided to summarize_pdf_openai.")
        return "Error: No content provided for summarization."

    messages.append({"role": "user", "content": content_list})

    try:
        logger.debug(f"Sending request to OpenAI model: {model_id}")
        response = await client.chat.completions.create(
            model=model_id,
            messages=messages,
            max_tokens=1000,  # Adjust as needed
            temperature=0.5,
        )
        summary = response.choices[0].message.content
        logger.info(f"Received summary from OpenAI model {model_id}.")
        return summary.strip() if summary else ""

    except OpenAIError as e:
        logger.error(f"OpenAI API error during summarization: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during OpenAI summarization: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


async def summarize_pdf_google(
    model_id: str,
    text_content: Optional[str] = None,
    image_data: Optional[List[str]] = None,
) -> str:
    """Summarizes PDF content (text or images) using the Google Gemini API."""
    model = _get_google_client(model_id)  # Use getter
    if not model:
        raise HTTPException(status_code=503, detail=f"Google GenAI model '{model_id}' is unavailable or API key missing.")

    prompt_parts = []
    if text_content:
        prompt_parts.append(text_content)
        logger.info(f"Preparing Google request with text content ({len(text_content)} chars).")

    if image_data:
        for i, img_b64 in enumerate(image_data):
            try:
                # Decode base64 to bytes, then load with PIL
                img_bytes = base64.b64decode(img_b64)
                img = Image.open(io.BytesIO(img_bytes))
                # Gemini API expects PIL Image objects directly for multimodal input
                prompt_parts.append(img)
            except Exception as e:
                logger.error(f"Error processing image {i} for Google API: {e}", exc_info=True)
                # Skip corrupted images or handle as needed
                continue
        logger.info(f"Preparing Google request with {len(image_data)} images.")

    if not prompt_parts:
        logger.warning("No text or image content provided to summarize_pdf_google.")
        return "Error: No content provided for summarization."

    # Add the instruction part
    prompt_parts.insert(0, "Summarize the following medical document content accurately and concisely:")

    try:
        logger.debug(f"Sending request to Google model: {model_id}")
        # Use generate_content_async for async operation
        response = await model.generate_content_async(prompt_parts)

        # Check for safety ratings and blocks
        if response.prompt_feedback.block_reason:
            logger.error(f"Google API request blocked due to: {response.prompt_feedback.block_reason}")
            raise HTTPException(status_code=400, detail=f"Request blocked by Google API: {response.prompt_feedback.block_reason}")
        if not response.candidates:
            logger.error("Google API returned no candidates.")
            raise HTTPException(status_code=500, detail="Google API returned no response candidates.")

        summary = response.text
        logger.info(f"Received summary from Google model {model_id}.")
        return summary.strip()

    except genai.GoogleAPIError as e:
        logger.error(f"Google API error during summarization: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Google API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during Google summarization: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


async def summarize_pdf_anthropic(
    model_id: str,
    text_content: Optional[str] = None,
    image_data: Optional[List[str]] = None,
) -> str:
    """Summarizes PDF content (text or images) using the Anthropic Claude API."""
    client = _get_anthropic_client()  # Use getter
    messages = []
    content_list = []

    # --- Construct Content List ---
    if text_content:
        content_list.append({"type": "text", "text": text_content})
        logger.info(f"Preparing Anthropic request with text content ({len(text_content)} chars).")

    if image_data:
        for i, img_b64 in enumerate(image_data):
            # Anthropic expects image media type and base64 data separately
            try:
                # Minimal check: is it likely PNG or JPEG? Decode a few bytes if needed.
                # For now, assume PNG as it's common, but this could be improved.
                media_type = "image/png"  # Or determine dynamically
                content_list.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": img_b64,
                        },
                    }
                )
            except Exception as e:
                logger.error(f"Error processing image {i} for Anthropic API: {e}", exc_info=True)
                continue  # Skip problematic images
        logger.info(f"Preparing Anthropic request with {len(image_data)} images.")

    if not content_list:
        logger.warning("No text or image content provided to summarize_pdf_anthropic.")
        return "Error: No content provided for summarization."

    messages.append({"role": "user", "content": content_list})

    try:
        logger.debug(f"Sending request to Anthropic model: {model_id}")
        response = await client.messages.create(
            model=model_id,
            system="You are an expert medical assistant. Summarize the provided medical document content accurately and concisely.",
            messages=messages,
            max_tokens=1000,  # Adjust as needed
            temperature=0.5,
        )

        # Extract text content from the response blocks
        summary = ""
        for block in response.content:
            if block.type == 'text':
                summary += block.text

        logger.info(f"Received summary from Anthropic model {model_id}.")
        return summary.strip()

    except AnthropicError as e:
        logger.error(f"Anthropic API error during summarization: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Anthropic API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during Anthropic summarization: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


# --- Main Router Function --- #
# Note: summarize_pdf_auto remains largely the same, calling the refactored functions

async def summarize_pdf_auto(
    provider: Literal["openai", "google", "anthropic"],
    model_id: str,
    pdf_file: UploadFile,
) -> str:
    # ... (implementation remains the same, calls the refactored functions)
    pass


# --- Added Functions (Placeholder - Need actual implementation) --- #

def get_llm_client(provider: str) -> Any:  # Return type Any for now
    """Returns the appropriate LLM client based on the provider."""
    if provider == "openai":
        return _get_openai_client()
    elif provider == "anthropic":
        return _get_anthropic_client()
    elif provider == "google":
        # Google client access might need more context (specific model?)
        # For now, check configuration status. A specific model client is fetched later.
        if _configure_google_genai():
            return genai  # Return the configured module/object
        else:
            raise ValueError("Google GenAI is not configured or API key is missing.")
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


async def summarize_text_with_llm(provider: str, model_id: str, text: str) -> str:
    """Summarizes plain text using the specified LLM provider and model."""
    logger.info(f"Summarizing text ({len(text)} chars) with {provider}:{model_id}")
    if provider == "openai":
        # Simplified call, assuming text-only input for this function
        return await summarize_pdf_openai(model_id=model_id, text_content=text)
    elif provider == "anthropic":
        return await summarize_pdf_anthropic(model_id=model_id, text_content=text)
    elif provider == "google":
        return await summarize_pdf_google(model_id=model_id, text_content=text)
    else:
        raise ValueError(f"Unsupported provider for text summarization: {provider}")


async def analyze_image_with_llm(provider: str, model_id: str, image_b64: str) -> str:
    """Analyzes a single base64 encoded image using the specified LLM provider and model."""
    logger.info(f"Analyzing image (base64) with {provider}:{model_id}")
    if provider == "openai":
        # Simplified call, assuming single image input
        return await summarize_pdf_openai(model_id=model_id, image_data=[image_b64])
    elif provider == "anthropic":
        return await summarize_pdf_anthropic(model_id=model_id, image_data=[image_b64])
    elif provider == "google":
        return await summarize_pdf_google(model_id=model_id, image_data=[image_b64])
    else:
        raise ValueError(f"Unsupported provider for image analysis: {provider}")
