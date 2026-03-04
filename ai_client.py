"""
AI client — tries Gemini first, falls back to Groq if Gemini fails.
"""
import logging
import time
from typing import Optional

from google import genai  # <- НОВЕ: замість google.generativeai
from groq import Groq

from config import (
    GEMINI_API_KEY, GROQ_API_KEY,
    GEMINI_MODEL, GROQ_MODEL, SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)


def _call_gemini(prompt: str) -> Optional[str]:
    """Call Google Gemini API."""
    if not GEMINI_API_KEY:
        logger.warning("Gemini API key not set, skipping.")
        return None
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={
                "system_instruction": SYSTEM_PROMPT,
                "temperature": 0.85,
                "max_output_tokens": 1200,
            }
        )
        text = response.text.strip()
        logger.info("Gemini responded OK (%d chars)", len(text))
        return text
    except Exception as e:
        logger.error("Gemini error: %s", e)
        return None


def _call_groq(prompt: str) -> Optional[str]:
    """Call Groq API (fallback)."""
    if not GROQ_API_KEY:
        logger.warning("Groq API key not set, skipping.")
        return None
    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1200,
            temperature=0.85,
        )
        text = response.choices[0].message.content.strip()
        logger.info("Groq responded OK (%d chars)", len(text))
        return text
    except Exception as e:
        logger.error("Groq error: %s", e)
        return None


def generate(prompt: str, retries: int = 2) -> Optional[str]:
    """
    Generate content using AI.
    Priority: Gemini → Groq → None (caller will use fallback post).
    """
    for attempt in range(retries):
        result = _call_gemini(prompt)
        if result:
            return result
        logger.warning("Gemini attempt %d/%d failed, trying Groq…", attempt + 1, retries)

        result = _call_groq(prompt)
        if result:
            return result
        logger.warning("Groq attempt %d/%d failed.", attempt + 1, retries)

        if attempt < retries - 1:
            time.sleep(3)

    logger.error("All AI providers failed after %d retries.", retries)
    return None
