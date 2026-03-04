"""
Post 2 — Daily Quiz (10:00 UTC)
Telegram Quiz Mode poll — grammar/vocabulary alternates daily.
"""
import json
import logging
import random
import re

from ai_client import generate
from utils.redis_client import get_day_counter, increment_day_counter, get_history, add_to_history, log_post_published
from utils.telegram_sender import send_quiz, send_message
from fallback_posts import FALLBACK_QUIZ

logger = logging.getLogger(__name__)


def _build_prompt(topic: str, used_topics: list[str]) -> str:
    return f"""Create a Telegram Quiz Mode poll for an English learning channel.
Topic type today: {topic}
Avoid these recently used quiz topics: {used_topics[:20]}

Respond ONLY with a valid JSON object — no extra text, no markdown fences.

{{
  "question": "Quiz question here (max 255 chars)",
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "correct_index": 0,
  "explanation": "Brief explanation in English + Ukrainian translation (max 180 chars total)",
  "topic_tag": "short topic name for history (e.g. 'present perfect' or 'synonyms of important')"
}}

Rules:
- question: clear, one sentence, B2/C1 level
- options: 4 plausible answers, only 1 correct
- correct_index: 0-based integer (0, 1, 2, or 3)
- explanation: starts with ✅ correct answer, then short reason
- For grammar: test a real exam mistake (conditionals, articles, tenses, etc.)
- For vocabulary: test synonyms, word forms, collocations
- Shuffle so correct answer is not always option 0
"""


def _parse_quiz_json(text: str) -> dict | None:
    """Extract JSON from AI response, even if wrapped in markdown."""
    text = text.strip()
    # Remove possible ```json ... ``` fences
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        # Validate required fields
        assert "question" in data
        assert "options" in data and len(data["options"]) == 4
        assert "correct_index" in data
        return data
    except Exception as e:
        logger.error("JSON parse error: %s | raw: %s", e, text[:200])
        return None


def post_daily_quiz() -> bool:
    logger.info("Generating Daily Quiz post…")

    # Alternate grammar / vocabulary each day
    day = get_day_counter("quiz_day")
    topic = "grammar" if day % 2 == 1 else "vocabulary"

    used_topics = get_history("quiz_topic")
    prompt = _build_prompt(topic, used_topics)

    content_raw = generate(prompt)
    quiz_data = None

    if content_raw:
        quiz_data = _parse_quiz_json(content_raw)

    if not quiz_data:
        logger.warning("AI failed or bad JSON — using fallback quiz.")
        quiz_data = random.choice(FALLBACK_QUIZ)

    # СПОЧАТКУ текст з хештегами
    tag = "#Grammar" if topic == "grammar" else "#Vocabulary"
    intro_text = f"🎯 <b>Daily Quiz</b> — {tag}\n\n{tag} #DailyQuiz #DailyEnglish #LearnEnglish"
    send_message(intro_text)

    # ПОТІМ сам квіз
    success = send_quiz(
        question=quiz_data["question"],
        options=quiz_data["options"],
        correct_index=quiz_data["correct_index"],
        explanation=quiz_data.get("explanation", ""),
    )

    if success:
        increment_day_counter("quiz_day")
        topic_tag = quiz_data.get("topic_tag", topic)
        add_to_history("quiz_topic", topic_tag)

    log_post_published("daily_quiz", success)
    return success
