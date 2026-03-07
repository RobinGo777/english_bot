import os

# ── Telegram ──────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]  # e.g. "@mychannel" or "-100123456789"

# ── AI APIs ───────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# ── Redis (history storage) ────────────────────────────────
REDIS_URL = os.environ["REDIS_URL"]  # e.g. redis://default:password@redis-host:6379

# ── Schedule (UTC) ────────────────────────────────────────
# 08:00 UTC = 10:00/11:00 Kyiv time
SCHEDULE = {
    "morning_boost": "08:00",
    "daily_quiz":    "10:00",
    "exam_prep":     "12:00",
    "thematic":      "14:00",
}

# ── Content settings ──────────────────────────────────────
HISTORY_DAYS = 90          # don't repeat topics within N days
VOCAB_LIST_SIZE = 15       # words in thematic vocabulary list

# ── AI model names ────────────────────────────────────────
GEMINI_MODEL = "models/gemini-2.5-flash"
GROQ_MODEL   = "llama-3.3-70b-versatile"   # free tier Groq model

# ── System prompt for all AI calls ───────────────────────
SYSTEM_PROMPT = """You are an expert English language teacher creating educational Telegram channel posts.

RULES:
- Use B2/C1 level English (except vocabulary lists — any level allowed)
- NEVER repeat words, phrases, or topics used in the last 90 days
- Use emojis for structure
- Format: **bold** for key words/phrases, `monospace` for IPA transcription
- Transcription: International Phonetic Alphabet (IPA) only
- Always include Ukrainian translation
- Examples must be practical and contemporary
- For Quiz Mode: 1 correct answer + 3 plausible wrong answers
- Tone: professional but friendly
- Always end with relevant hashtags
- Write post content only — no meta-commentary or explanations outside the post"""
