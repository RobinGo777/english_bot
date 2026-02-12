"""
main.py — Entry point for the English Learning Telegram Bot.

Schedule (UTC):
  08:00 → Morning Boost
  10:00 → Daily Quiz
  12:00 → Exam Prep
  14:00 → Thematic Content

Run: python main.py
"""
import logging
import os
import sys
import time
from datetime import datetime

import schedule

# ── Logging setup ─────────────────────────────────────────
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("main")

# ── Imports after logging setup ───────────────────────────
from utils.redis_client import ping as redis_ping, log_post_published
from utils.telegram_sender import send_welcome
from content.post1_morning import post_morning_boost
from content.post2_quiz import post_daily_quiz
from content.post3_exam import post_exam_prep
from content.post4_thematic import post_thematic


def safe_run(fn, post_type: str):
    """Wrap a post function with error handling and logging."""
    logger.info("▶ Starting: %s", post_type)
    try:
        success = fn()
        status = "✅ OK" if success else "⚠️ Failed (sent fallback)"
        logger.info("%s | %s", post_type, status)
        log_post_published(post_type, success)
    except Exception as e:
        logger.error("❌ CRASH in %s: %s", post_type, e, exc_info=True)
        log_post_published(post_type, False, str(e))


def job_morning():
    safe_run(post_morning_boost, "morning_boost")

def job_quiz():
    safe_run(post_daily_quiz, "daily_quiz")

def job_exam():
    safe_run(post_exam_prep, "exam_prep")

def job_thematic():
    safe_run(post_thematic, "thematic")


def startup_checks():
    """Verify all required services are reachable before starting."""
    logger.info("═" * 50)
    logger.info("English Bot starting up…")
    logger.info("═" * 50)

    # Check Redis
    if redis_ping():
        logger.info("✅ Redis connection OK")
    else:
        logger.critical("❌ Redis connection FAILED — exiting.")
        sys.exit(1)

    # Check Telegram token
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        logger.critical("❌ TELEGRAM_BOT_TOKEN not set — exiting.")
        sys.exit(1)
    logger.info("✅ Telegram token present")

    # Check at least one AI key
    gemini = os.environ.get("GEMINI_API_KEY", "")
    groq   = os.environ.get("GROQ_API_KEY", "")
    if not gemini and not groq:
        logger.warning("⚠️  No AI API keys set — bot will only use fallback posts.")
    elif gemini:
        logger.info("✅ Gemini API key present")
    elif groq:
        logger.info("✅ Groq API key present (Gemini not set)")

    logger.info("═" * 50)


def send_welcome_if_needed():
    """Send welcome post only once (checked via Redis flag)."""
    from utils.redis_client import get_client
    r = get_client()
    if not r.get("welcome_sent"):
        logger.info("Sending welcome post…")
        ok = send_welcome()
        if ok:
            r.set("welcome_sent", "1")
            logger.info("Welcome post sent and flagged.")
        else:
            logger.warning("Welcome post failed — will retry on next startup.")


def main():
    startup_checks()
    send_welcome_if_needed()

    # ── Schedule jobs ─────────────────────────────────────
    schedule.every().day.at("08:00").do(job_morning)
    schedule.every().day.at("10:00").do(job_quiz)
    schedule.every().day.at("12:00").do(job_exam)
    schedule.every().day.at("14:00").do(job_thematic)

    logger.info("Scheduler running. Posts scheduled at 08:00, 10:00, 12:00, 14:00 UTC")
    logger.info("(= 10:00, 12:00, 14:00, 16:00 Kyiv time in winter)")
    logger.info("Press Ctrl+C to stop.\n")

    while True:
        schedule.run_pending()
        time.sleep(30)  # check every 30 seconds


if __name__ == "__main__":
    # Allow manual post testing: python main.py test morning
    if len(sys.argv) == 3 and sys.argv[1] == "test":
        post_map = {
            "morning":  job_morning,
            "quiz":     job_quiz,
            "exam":     job_exam,
            "thematic": job_thematic,
            "welcome":  send_welcome,
        }
        key = sys.argv[2]
        if key in post_map:
            startup_checks()
            logger.info("Running test post: %s", key)
            post_map[key]()
        else:
            print(f"Unknown post type. Choose from: {list(post_map.keys())}")
        sys.exit(0)

    main()
