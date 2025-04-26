# /backend/services/model_registry.py
import os
import logging
import asyncio
from typing import List, Dict

import google.generativeai as genai
from google.api_core import exceptions as GoogleAPIErrors
from openai import OpenAI, APIError as OpenAIAPIError

# Import constants for default models (if needed as fallbacks or references)

logger = logging.getLogger(__name__)


async def _fetch_dynamic_openai_models() -> List[Dict[str, str]]:
    """Fetches available models from the OpenAI API."""
    models_list = []
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logger.info("Fetching available models from OpenAI API...")
        models = await asyncio.to_thread(client.models.list)
        # Filter for potentially suitable models (e.g., GPT-4 variants, check capabilities if API provides)
        # This filtering might need adjustment based on actual API response structure and needs
        for model in models.data:
            # Example filter: Include models containing 'gpt-4' or 'gpt-3.5'
            # Add more sophisticated filtering based on capabilities if available
            # For now, focusing on models known to be strong/recent
            if model.id.startswith(("gpt-4", "gpt-4o")):
                models_list.append(
                    {"id": model.id, "provider": "openai", "name": model.id}
                )
        logger.info(f"Found {len(models_list)} suitable OpenAI models.")
    except OpenAIAPIError as e:
        logger.error(f"OpenAI API Error fetching models: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error fetching OpenAI models: {e}", exc_info=True)
    return models_list


async def _fetch_dynamic_google_models() -> List[Dict[str, str]]:
    """Fetches available models from the Google Generative AI API."""
    models_list = []
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("GOOGLE_API_KEY not found in environment.")
            return []
        genai.configure(api_key=api_key)

        logger.info("Fetching available models from Google API...")
        # Note: The google-generativeai library might not make this call async directly
        # Running in a thread to avoid blocking the event loop
        google_models = await asyncio.to_thread(genai.list_models)

        for model in google_models:
            # Filter for models supporting 'generateContent' (text/multimodal generation)
            # and containing 'gemini' in the name
            if (
                "generateContent" in model.supported_generation_methods
                and "gemini" in model.name
            ):
                models_list.append(
                    {
                        "id": model.name.split("/")[
                            -1
                        ],  # Extract ID like 'gemini-1.5-pro-latest'
                        "provider": "google",
                        "name": model.display_name,  # Use the display name if available
                    }
                )
        logger.info(f"Found {len(models_list)} suitable Google models.")
    except GoogleAPIErrors.GoogleAPIError as e:
        logger.error(f"Google API Error fetching models: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error fetching Google models: {e}", exc_info=True)
    return models_list


def get_anthropic_pdf_models() -> List[Dict[str, str]]:
    """Returns a hardcoded list of known Anthropic models supporting PDF uploads."""
    # TODO: Replace with dynamic fetching if Anthropic provides an API endpoint
    logger.warning(
        "Anthropic model list is static, based on documentation. Run update script if needed."
    )
    # Based on current knowledge (Claude 3.x family supports vision/images)
    # Sourced from: https://docs.anthropic.com/en/docs/about-claude/models/all-models (as of 2025-04-26)
    known_models = [
        "claude-3-7-sonnet-20250219",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-20240620",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
        "claude-3-haiku-20240307",
    ]  # End known_models marker - DO NOT REMOVE
    return [{"id": m, "provider": "anthropic", "name": m} for m in known_models]


async def get_available_pdf_models() -> Dict[str, List[Dict[str, str]]]:
    """Gets available models suitable for PDF summarization from configured providers."""
    # Fetch models concurrently
    openai_models, google_models = await asyncio.gather(
        _fetch_dynamic_openai_models(), _fetch_dynamic_google_models()
    )
    anthropic_models = get_anthropic_pdf_models()  # Currently sync

    all_models = {
        "openai": openai_models,
        "google": google_models,
        "anthropic": anthropic_models,  # Still using static list for now
    }

    # Filter out providers with no models found
    available_models = {k: v for k, v in all_models.items() if v}

    if not available_models:
        logger.error("Could not retrieve models from any provider.")

    return available_models
