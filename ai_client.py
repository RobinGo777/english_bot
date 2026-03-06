"""
AI client — tries Gemini Pro first, then Gemini Flash, then Groq.
"""
import logging
import time
from typing import Optional

from google import genai
from groq import Groq

# Оновіть ваш config.py, додавши GEMINI_PRO_MODEL = "models/gemini-3.1-pro"
from config import (
    GEMINI_API_KEY, GROQ_API_KEY,
    GEMINI_MODEL, GROQ_MODEL, SYSTEM_PROMPT,
)

# Додаємо константу для Pro моделі, якщо її немає в config
GEMINI_PRO_MODEL = "models/gemini-3.1-pro"

logger = logging.getLogger(__name__)

# Ініціалізація клієнтів (Singleton style)
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def _call_gemini(prompt: str, model_name: str) -> Optional[str]:
    """Універсальний виклик для будь-якої моделі Gemini."""
    if not gemini_client:
        logger.warning("Gemini client not initialized, skipping.")
        return None
    try:
        response = gemini_client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={
                "system_instruction": SYSTEM_PROMPT,
                "temperature": 0.85,
                "max_output_tokens": 1200,
            }
        )
        text = response.text.strip()
        logger.info("%s responded OK (%d chars)", model_name, len(text))
        return text
    except Exception as e:
        logger.error("%s error: %s", model_name, e)
        return None

def _call_groq(prompt: str) -> Optional[str]:
    """Виклик Groq API (останній рубеж захисту)."""
    if not groq_client:
        logger.warning("Groq client not initialized, skipping.")
        return None
    try:
        response = groq_client.chat.completions.create(
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
    Генерація контенту з ієрархією моделей:
    1. Gemini 3.1 Pro (найкраща якість тексту)
    2. Gemini 3 Flash (ваша основна швидка модель)
    3. Groq (Llama 3.3 як fallback)
    """
    
    # Список моделей Google за пріоритетом
    gemini_models = [GEMINI_PRO_MODEL, GEMINI_MODEL]

    for attempt in range(retries):
        # Крок 1: Пробуємо Gemini (спочатку Pro, потім Flash)
        for model in gemini_models:
            result = _call_gemini(prompt, model)
            if result:
                return result
            
            # Якщо отримали помилку, трохи чекаємо перед наступною моделлю/спробою
            time.sleep(1) 

        # Крок 2: Якщо Gemini не відповіли, пробуємо Groq
        logger.warning("Gemini attempt %d/%d failed, trying Groq...", attempt + 1, retries)
        result = _call_groq(prompt)
        if result:
            return result
        
        logger.warning("Groq attempt %d/%d failed.", attempt + 1, retries)

        # Пауза перед повним перезапуском циклу спроб
        if attempt < retries - 1:
            wait_time = (attempt + 1) * 3  # Збільшуємо паузу: 3с, 6с...
            time.sleep(wait_time)

    logger.error("All AI providers (Gemini Pro, Flash, Groq) failed after %d retries.", retries)
    return None
