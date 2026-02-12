"""
Post 1 — Morning Boost (08:00 UTC)
Contains: Word of the Day, Phrase of the Day, Collocation of the Day
No rotation — published every day.
"""
import logging

from ai_client import generate
from utils.redis_client import get_history, add_to_history
from utils.telegram_sender import send_message
from fallback_posts import FALLBACK_MORNING

logger = logging.getLogger(__name__)


def _build_prompt(used_words: list[str], used_phrases: list[str], used_collocations: list[str]) -> str:
    return f"""Create a "Morning Boost" Telegram post for an English learning channel.

AVOID these already-used words: {used_words[:30]}
AVOID these already-used phrases: {used_phrases[:30]}
AVOID these already-used collocations: {used_collocations[:30]}

The post must have EXACTLY this structure (use HTML formatting for Telegram):

📌 <b>Word of the Day</b>
<b>[WORD]</b> — `[IPA]` — [Ukrainian translation]
📖 [Example sentence at B2/C1 level]
#WordOfTheDay

💬 <b>Phrase of the Day</b>
<b>[PHRASE]</b> — [Ukrainian translation]
📌 [Context / when to use it]
🗣 [Short example dialogue 2 lines]
#PhraseOfTheDay

🔗 <b>Collocation of the Day</b>
<b>[COLLOCATION]</b> — [Ukrainian translation]
• [Example sentence 1]
• [Example sentence 2]
• [Example sentence 3]
#Collocation

#DailyEnglish #LearnEnglish

Rules:
- Use HTML tags: <b>bold</b>, <code>monospace</code> for IPA (not backticks)
- B2/C1 vocabulary for word & phrase, practical usage
- Ukrainian translations on the same line after em dash
- Keep total length under 900 characters
"""


def post_morning_boost() -> bool:
    logger.info("Generating Morning Boost post…")

    used_words        = get_history("word_of_day")
    used_phrases      = get_history("phrase_of_day")
    used_collocations = get_history("collocation")

    prompt = _build_prompt(used_words, used_phrases, used_collocations)
    content = generate(prompt)

    if not content:
        logger.warning("AI failed — using fallback Morning Boost post.")
        import random
        content = random.choice(FALLBACK_MORNING)

    success = send_message(content)

    if success:
        # Best-effort: extract the word/phrase/collocation from AI output
        # We'll just log the first word found between <b> tags as approximation
        import re
        bold_items = re.findall(r"<b>([^<]+)</b>", content)
        if len(bold_items) >= 1:
            add_to_history("word_of_day", bold_items[0])
        if len(bold_items) >= 2:
            add_to_history("phrase_of_day", bold_items[1])
        if len(bold_items) >= 3:
            add_to_history("collocation", bold_items[2])

    return success
