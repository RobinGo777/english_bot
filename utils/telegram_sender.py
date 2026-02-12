"""
Telegram sender — sends text posts and Quiz Mode polls to the channel.
"""
import logging
from typing import Optional

import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

logger = logging.getLogger(__name__)

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_message(text: str, parse_mode: str = "HTML") -> bool:
    """Send a text message to the channel."""
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        data = r.json()
        if data.get("ok"):
            logger.info("Message sent to channel.")
            return True
        else:
            logger.error("Telegram error: %s", data)
            return False
    except Exception as e:
        logger.error("send_message exception: %s", e)
        return False


def send_quiz(
    question: str,
    options: list[str],
    correct_index: int,
    explanation: str = "",
) -> bool:
    """
    Send a Quiz Mode poll (Telegram native quiz).
    - question: quiz question text
    - options: list of 4 answer strings
    - correct_index: 0-based index of the correct answer
    - explanation: shown after user answers (max 200 chars in Telegram)
    """
    url = f"{BASE_URL}/sendPoll"
    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "question": question,
        "options": options,
        "type": "quiz",
        "correct_option_id": correct_index,
        "is_anonymous": True,
        "explanation": explanation[:200] if explanation else "",
        "explanation_parse_mode": "HTML",
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        data = r.json()
        if data.get("ok"):
            logger.info("Quiz poll sent to channel.")
            return True
        else:
            logger.error("Telegram quiz error: %s", data)
            return False
    except Exception as e:
        logger.error("send_quiz exception: %s", e)
        return False


def send_welcome() -> bool:
    """Send the one-time welcome post."""
    text = (
        "👋 <b>Ласкаво просимо до каналу!</b>\n\n"
        "Тут ви знайдете:\n"
        "📚 Щоденні слова та фрази\n"
        "🎯 Квізи з граматики та лексики\n"
        "✈️ Англійська для подорожей\n"
        "🎓 Підготовка до IELTS/TOEFL\n\n"
        "<b>Графік публікацій (за Києвом):</b>\n"
        "⏰ 10:00 — Morning Boost\n"
        "⏰ 12:00 — Daily Quiz\n"
        "⏰ 14:00 — Exam Prep\n"
        "⏰ 16:00 — Тематичний контент\n\n"
        "#Welcome #LearnEnglish #DailyEnglish"
    )
    return send_message(text)
