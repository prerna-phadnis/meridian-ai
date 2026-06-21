# src/lib/gemini.py
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logger = logging.getLogger(__name__)

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

FLASH_MODEL = "gemini-2.5-flash"
PRO_MODEL = "gemini-2.5-pro"


def generate_text(
    prompt: str,
    model: str = FLASH_MODEL,
    temperature: float = 0.2,
    max_tokens: int = 2000,
    json_mode: bool = False
) -> str:
    """
    Simple text generation.
    Use this for notes, citations, summaries.
    """

    config_params = {
        "temperature": temperature,
        "max_output_tokens": max_tokens,
        # gemini-2.5+ models think by default, and thinking tokens count
        # against max_output_tokens — causing truncated/invalid JSON on
        # structured-output tasks like this. We don't need reasoning for
        # extraction/formatting, so turn it off.
        "thinking_config": types.ThinkingConfig(thinking_budget=0),
    }

    if json_mode:
        config_params["response_mime_type"] = "application/json"

    config = types.GenerateContentConfig(**config_params)

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config
    )

    return response.text


def generate_text_with_system(
    system_prompt: str,
    user_prompt: str,
    model: str = FLASH_MODEL,
    temperature: float = 0.2,
    max_tokens: int = 2000,
    json_mode: bool = False
) -> str:
    """
    Generation with system + user prompt.
    Use this for RAG chat.
    """

    config_params = {
        "temperature": temperature,
        "max_output_tokens": max_tokens,
        "system_instruction": system_prompt,
        "thinking_config": types.ThinkingConfig(thinking_budget=0),
    }

    if json_mode:
        config_params["response_mime_type"] = "application/json"

    config = types.GenerateContentConfig(**config_params)

    response = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=config
    )

    return response.text