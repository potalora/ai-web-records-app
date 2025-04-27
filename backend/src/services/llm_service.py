import os
import asyncio
from typing import List, Literal, Optional
from fastapi import UploadFile, HTTPException
import base64
import logging

import google.generativeai as genai
from openai import AsyncOpenAI, APIError as OpenAIAPIError
from anthropic import AsyncAnthropic, APIError as AnthropicAPIError

# Import PDF utility functions
from .pdf_utils import analyze_pdf_content, convert_pdf_to_images

# Import constants for default models

# Configure basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

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
        logging.warning(
            "Google API Key not found. Google models will not be available."
        )
        genai = None  # Disable Google features if key is missing
except Exception as e:
    logging.error(f"Failed to configure Google GenAI client: {e}")
    genai = None

logger = logging.getLogger(__name__)

# --- Summarization Functions ---

SUMMARIZATION_PROMPT = "Summarize the following medical record content, focusing on key diagnoses, treatments, medications, and allergies:"
IMAGE_SUMMARIZATION_PROMPT = "Analyze the following medical document page image(s) and provide a concise summary, focusing on key diagnoses, treatments, medications, and allergies mentioned or depicted."


async def summarize_pdf_openai(
    model_id: str,
    text_content: Optional[str] = None,
    image_data: Optional[List[str]] = None,
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
            {
                "role": "system",
                "content": "You are a helpful medical assistant specializing in summarizing records.",
            },
            {"role": "user", "content": f"{SUMMARIZATION_PROMPT}\n\n{text_content}"},
        ]
    elif image_data:
        logger.debug(f"Building OpenAI request for {len(image_data)} image(s).")
        # Construct messages for OpenAI API (multi-modal)
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": IMAGE_SUMMARIZATION_PROMPT},
                    *[
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                        }
                        for img_b64 in image_data
                    ],
                ],
            }
        ]

    try:
        response = await openai_client.chat.completions.create(
            model=model_id,
            messages=messages,
            max_tokens=1024,  # Adjust as needed
        )
        summary = response.choices[0].message.content
        logger.info(f"Successfully received summary from OpenAI model {model_id}.")
        return summary.strip() if summary else ""
    except OpenAIAPIError as e:
        logging.error(
            f"OpenAI API Error using model {model_id}: Status={e.status_code}, Message={e.message}",
            exc_info=True,
        )
        # Consider extracting more details if available in e.body or e.response
        raise  # Re-raise the original error for main.py to handle
    except Exception as e:
        logging.error(
            f"Error during OpenAI summarization using model {model_id}: {e}",
            exc_info=True,
        )
        raise


async def summarize_pdf_google(
    model_id: str,
    text_content: Optional[str] = None,
    image_data: Optional[List[str]] = None,
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
            image_part = {"mime_type": "image/png", "data": img_bytes}
            parts.append(image_part)
            logger.debug(f"Added image {i + 1} to Google request.")

    logger.info(f"Sending request to Google model {model_id}...")
    # Note: Gemini API calls are synchronous in the current library version
    # We might run this in a threadpool executor for true async behavior if needed
    response = await asyncio.to_thread(
        genai.GenerativeModel(model_id).generate_content, parts
    )

    summary = response.text
    logger.info(f"Successfully received summary from Google model {model_id}.")
    return summary.strip() if summary else ""


async def summarize_pdf_anthropic(
    model_id: str,
    text_content: Optional[str] = None,
    image_data: Optional[List[str]] = None,
) -> str:
    """Summarizes PDF content (text or images) using the Anthropic Claude API."""
    # Implementation pending adaptation
    if not text_content and not image_data:
        raise ValueError(
            "Either text_content or image_data must be provided for Anthropic."
        )
    if text_content and image_data:
        raise ValueError(
            "Provide either text_content or image_data for Anthropic, not both."
        )

    logger.info(f"Summarizing with Anthropic model: {model_id}")
    target_model = model_id  # Use the provided model_id directly

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
                content_blocks.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img_b64,
                        },
                    }
                )
            messages = [{"role": "user", "content": content_blocks}]

        logger.info(f"Sending request to Anthropic model {target_model}...")
        response = await anthropic_client.messages.create(
            model=target_model, max_tokens=1024, messages=messages
        )
        summary = ""
        if response.content and isinstance(response.content, list):
            # Find the first text block in the response
            for block in response.content:
                if hasattr(block, "text"):
                    summary = block.text
                    break

        logger.info(
            f"Successfully received summary from Anthropic model {target_model}."
        )
        return summary.strip() if summary else ""
    except AnthropicAPIError as e:
        logging.error(
            f"Anthropic API Error using model {target_model}: Status={e.status_code}, Message={e.message}",
            exc_info=True,
        )
        raise
    except Exception as e:
        logging.error(
            f"Error during Anthropic summarization using model {target_model}: {e}",
            exc_info=True,
        )
        raise


# --- Main Router Function ---


async def summarize_pdf_auto(
    provider: Literal["openai", "google", "anthropic"],
    model_id: str,
    pdf_file: UploadFile,
) -> str:
    """Summarizes a PDF using the specified provider and model, automatically handling text vs. image PDFs."""
    logger.info(
        f"Starting PDF summarization with {provider=}, {model_id=}, filename='{pdf_file.filename}'."
    )
    try:
        pdf_content = await pdf_file.read()
        if not pdf_content:
            logger.error("Uploaded PDF file is empty.")
            raise HTTPException(status_code=400, detail="Uploaded PDF file is empty.")

        logger.info("Analyzing PDF content...")
        pdf_type, extracted_text = analyze_pdf_content(pdf_content)

        summary = ""
        if pdf_type == "text" and extracted_text:
            logger.info(
                f"Processing PDF as text. Extracted {len(extracted_text)} characters."
            )
            if provider == "openai":
                # TODO: Update summarize_pdf_openai to accept text_content
                summary = await summarize_pdf_openai(
                    model_id, text_content=extracted_text
                )
            elif provider == "google":
                # TODO: Update summarize_pdf_google to accept text_content
                summary = await summarize_pdf_google(
                    model_id, text_content=extracted_text
                )
            elif provider == "anthropic":
                # TODO: Update summarize_pdf_anthropic to accept text_content
                summary = await summarize_pdf_anthropic(
                    model_id, text_content=extracted_text
                )
        elif pdf_type == "image":
            logger.info("Processing PDF as image. Converting pages...")
            base64_images = convert_pdf_to_images(pdf_content)
            if not base64_images:
                logger.error("Failed to convert PDF to images.")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to convert PDF to images. The file might be corrupted or require OCR.",
                )

            logger.info(
                f"Successfully converted PDF to {len(base64_images)} images. Sending to provider..."
            )
            if provider == "openai":
                # TODO: Update summarize_pdf_openai to accept image_data
                summary = await summarize_pdf_openai(model_id, image_data=base64_images)
            elif provider == "google":
                # TODO: Update summarize_pdf_google to accept image_data
                summary = await summarize_pdf_google(model_id, image_data=base64_images)
            elif provider == "anthropic":
                # TODO: Update summarize_pdf_anthropic to accept image_data
                summary = await summarize_pdf_anthropic(
                    model_id, image_data=base64_images
                )
        else:
            # Should not happen if analyze_pdf_content is correct
            logger.error(f"Unexpected pdf_type '{pdf_type}' from analyze_pdf_content.")
            raise HTTPException(
                status_code=500, detail="Internal server error during PDF analysis."
            )

        logger.info(
            f"Successfully generated summary using {provider} model {model_id}."
        )
        return summary

    except HTTPException as http_exc:
        logger.error(f"HTTP Exception during PDF summarization: {http_exc}")
        raise
    except Exception as e:
        logger.error(f"Error during PDF summarization: {e}", exc_info=True)
        raise
