"""
Post 4 — Thematic Content (14:00 UTC)
Odd days  → Vocabulary List (rotating topics)
Even days → Travel English (8 sub-categories rotating)
"""
import logging
import random

from ai_client import generate
from utils.redis_client import get_day_counter, increment_day_counter, get_history, add_to_history, log_post_published
from utils.telegram_sender import send_message
from fallback_posts import FALLBACK_THEMATIC
from utils.transcription import get_ipa

logger = logging.getLogger(__name__)


# ── Vocabulary topics list ────────────────────────────────
VOCAB_TOPICS = [
    ("Food & Cooking", "🍕", "food"),
    ("Travel & Tourism", "✈️", "travel"),
    ("Work & Career", "💼", "work"),
    ("Nature & Environment", "🌿", "nature"),
    ("Technology & Innovation", "💻", "technology"),
    ("Emotions & Feelings", "💭", "emotions"),
    ("Sports & Fitness", "⚽", "sports"),
    ("Art & Culture", "🎨", "art"),
    ("Science & Research", "🔬", "science"),
    ("Home & Daily Life", "🏠", "home"),
    ("Health & Medicine", "🏥", "medicine"),
    ("Education & Learning", "📖", "education"),
    ("Finance & Economics", "💰", "finance"),
    ("Fashion & Style", "👗", "fashion"),
    ("Transport & Vehicles", "🚗", "transport"),
    ("Politics & Society", "🌍", "politics"),
    ("Food Idioms", "🍽️", "food_idioms"),
    ("Business English", "📊", "business"),
]

# ── Travel sub-categories ─────────────────────────────────
TRAVEL_SUBS = [
    ("Travel Phrases of the Day",    "🌍", "travel_phrases"),
    ("Airport English",              "🛫", "airport"),
    ("Hotel Check-in Vocabulary",    "🏨", "hotel"),
    ("Restaurant English",           "🍽️", "restaurant"),
    ("Public Transport Phrases",     "🚌", "transport"),
    ("Emergency Situations",         "🆘", "emergency"),
    ("Travel Idioms & Expressions",  "🗣️", "travel_idioms"),
    ("Survival Vocabulary",          "🎒", "survival"),
]


# ── Prompts ───────────────────────────────────────────────

def _prompt_vocab_list(topic_name: str, emoji: str, used_words: list[str]) -> str:
    return f"""Create a vocabulary list Telegram post about "{topic_name}" for an English learning channel.
Avoid these already-used words: {used_words[:40]}

Format (HTML for Telegram):
{emoji} <b>{topic_name}</b>

[List exactly 15 words in this format, one per line:]
<b>word</b> <code>/IPA/</code> — Ukrainian translation

[After the list:]
💡 <i>[One practical tip about this vocabulary topic in English + Ukrainian]</i>

#VocabularyList #Theme{topic_name.replace(" ", "")} #LearnEnglish #DailyEnglish

Rules:
- Mix of common and less-common words
- Include nouns, verbs, adjectives
- IPA transcription for each word (use standard IPA symbols)
- Ukrainian translation for each word
- Keep words practical and useful
"""


def _prompt_travel(sub_name: str, emoji: str, sub_key: str, used: list[str]) -> str:
    sub_instructions = {
        "travel_phrases": "5–7 essential travel phrases (greetings, asking for help, directions). Include a mini-dialogue.",
        "airport":        "Phrases for check-in, baggage drop, security, boarding. Include a dialogue between passenger and staff.",
        "hotel":          "Hotel check-in/out vocabulary, requesting services, room amenities. Include typical questions.",
        "restaurant":     "Phrases for ordering, asking about menu, paying. Include a dialogue with a waiter.",
        "transport":      "Bus, train, taxi phrases. Asking for tickets, routes, stops.",
        "emergency":      "Phrases for illness, lost documents, asking for help. Include emergency vocabulary.",
        "travel_idioms":  "5–7 travel-related idioms with meaning and example sentences.",
        "survival":       "Most essential phrases a traveller must know. Bare minimum vocabulary.",
    }
    instruction = sub_instructions.get(sub_key, "Useful travel phrases with examples.")
    return f"""Create a "Travel English" Telegram post about "{sub_name}" for an English learning channel.
Specific focus: {instruction}
Avoid recently used phrases: {used[:20]}

Format (HTML for Telegram):
{emoji} <b>{sub_name}</b>

[Content following the specific focus above]
Each phrase: <b>[English phrase]</b> — [Ukrainian translation]
Include context and/or a short dialogue where appropriate.

#TravelEnglish #{sub_key.replace("_", "").title()} #LearnEnglish #DailyEnglish

Rules: Practical, real-world English. B1–B2 level (travel English is accessible). Ukrainian translations required.
"""


# ── Main function ─────────────────────────────────────────

def post_thematic() -> bool:
    logger.info("Generating Thematic post…")

    day = get_day_counter("thematic_day")
    is_odd = (day % 2 == 1)

    if is_odd:
        # Vocabulary list — cycle through topics
        topic_idx = ((day - 1) // 2) % len(VOCAB_TOPICS)
        topic_name, emoji, topic_key = VOCAB_TOPICS[topic_idx]
        used = get_history(f"vocab_topic_{topic_key}")
        prompt = _prompt_vocab_list(topic_name, emoji, used)
        history_key = f"vocab_topic_{topic_key}"
        history_val = topic_name
        fallback_pool = FALLBACK_THEMATIC.get("vocab", [])
    else:
        # Travel English — cycle through 8 sub-categories
        travel_idx = ((day - 2) // 2) % len(TRAVEL_SUBS)
        sub_name, emoji, sub_key = TRAVEL_SUBS[travel_idx]
        used = get_history(f"travel_{sub_key}")
        prompt = _prompt_travel(sub_name, emoji, sub_key, used)
        history_key = f"travel_{sub_key}"
        history_val = sub_name
        fallback_pool = FALLBACK_THEMATIC.get("travel", [])

    content = generate(prompt)

    if not content:
        logger.warning("AI failed — using fallback Thematic post.")
        content = random.choice(fallback_pool) if fallback_pool else "⚙️ Content temporarily unavailable. Check back soon!"

    success = send_message(content)

    if success:
        increment_day_counter("thematic_day")
        add_to_history(history_key, history_val)

    log_post_published("thematic", success)
    return success
