"""
main.py — Entry point for the English Learning Telegram Bot.
"""
import logging
import os
import sys
import time
from threading import Thread
import schedule

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

from utils.redis_client import ping as redis_ping, log_post_published
from utils.telegram_sender import send_welcome
from content.post1_morning import post_morning_boost
from content.post2_quiz import post_daily_quiz
from content.post3_exam import post_exam_prep
from content.post4_thematic import post_thematic


def safe_run(fn, post_type: str):
    logger.info("▶ Starting: %s", post_type)
    try:
        success = fn()
        status = "✅ OK" if success else "⚠️ Failed"
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
    logger.info("═" * 50)
    logger.info("English Bot starting up…")
    logger.info("═" * 50)

    if redis_ping():
        logger.info("✅ Redis connection OK")
    else:
        logger.critical("❌ Redis FAILED")
        sys.exit(1)

    if not os.environ.get("TELEGRAM_BOT_TOKEN"):
        logger.critical("❌ TELEGRAM_BOT_TOKEN not set")
        sys.exit(1)
    logger.info("✅ Telegram token OK")

    gemini = os.environ.get("GEMINI_API_KEY")
    groq = os.environ.get("GROQ_API_KEY")
    if not gemini and not groq:
        logger.warning("⚠️  No AI keys — using fallback posts only")
    elif gemini:
        logger.info("✅ Gemini API key OK")
    elif groq:
        logger.info("✅ Groq API key OK")

    logger.info("═" * 50)


def send_welcome_if_needed():
    from utils.redis_client import get_client
    r = get_client()
    if not r.get("welcome_sent"):
        logger.info("Sending welcome post…")
        if send_welcome():
            r.set("welcome_sent", "1")
            logger.info("Welcome sent")


def run_scheduler():
    """Scheduler loop - runs in BACKGROUND thread."""
    schedule.every().day.at("08:00").do(job_morning)
    schedule.every().day.at("10:00").do(job_quiz)
    schedule.every().day.at("12:00").do(job_exam)
    schedule.every().day.at("14:00").do(job_thematic)

    logger.info("📅 Scheduler running at 08:00, 10:00, 12:00, 14:00 UTC")
    logger.info("   (= 10:00, 12:00, 14:00, 16:00 Kyiv)")

    while True:
        schedule.run_pending()
        time.sleep(30)


def keep_alive():
    """Ping ourselves every 10 minutes to prevent Render sleep."""
    import requests
    
    url = os.environ.get("RENDER_EXTERNAL_URL", "https://english-bot-38iy.onrender.com")
    
    while True:
        try:
            time.sleep(600)  # 10 minutes
            requests.get(url, timeout=10)
            logger.info("🔄 Keep-alive ping sent")
        except Exception as e:
            logger.warning("Keep-alive ping failed: %s", e)


def run_http_server():
    """HTTP server - runs in MAIN thread for Render."""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write('🤖 Bot is running'.encode('utf-8'))
        
        def log_message(self, *args):
            pass
    
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), Handler)
    logger.info(f"🌐 HTTP server running on port {port}")
    server.serve_forever()


def main():
    startup_checks()
    send_welcome_if_needed()

    # Start SCHEDULER in background thread
    scheduler_thread = Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # Start KEEP-ALIVE in background thread
    keepalive_thread = Thread(target=keep_alive, daemon=True)
    keepalive_thread.start()

    # Run HTTP server in MAIN thread (blocks forever)
    run_http_server()


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "test":
        post_map = {
            "morning": job_morning,
            "quiz": job_quiz,
            "exam": job_exam,
            "thematic": job_thematic,
            "welcome": send_welcome,
        }
        if sys.argv[2] in post_map:
            startup_checks()
            logger.info(f"Testing: {sys.argv[2]}")
            post_map[sys.argv[2]]()
        else:
            print(f"Options: {list(post_map.keys())}")
        sys.exit(0)

    main()
