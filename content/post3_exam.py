"""
Post 3 — Exam Prep (12:00 UTC)
Rotates across 4 sub-types: Vocabulary Upgrade → Tricky Pairs → Mini Grammar Quiz → Speaking Prompt
"""
import logging
import random

from ai_client import generate
from utils.redis_client import get_day_counter, increment_day_counter, get_history, add_to_history, log_post_published
from utils.telegram_sender import send_message
from fallback_posts import FALLBACK_EXAM

logger = logging.getLogger(__name__)


# ── Prompt builders ───────────────────────────────────────

def _prompt_vocab_upgrade(used: list[str]) -> str:
    return f"""Create an "Upgrade Your Vocabulary" Telegram post for an English learning channel.
Avoid recently used base words: {used[:20]}

Format (HTML for Telegram):
📚 <b>Upgrade Your Vocabulary</b>

🔹 Basic word: <b>[WORD]</b> — [Ukrainian]
⬆️ Academic alternatives:
• <b>[synonym1]</b> — [Ukrainian] — [Example sentence]
• <b>[synonym2]</b> — [Ukrainian] — [Example sentence]
• <b>[synonym3]</b> — [Ukrainian] — [Example sentence]

💡 <i>Tip: [short usage tip in English + Ukrainian]</i>

#ExamPrep #Vocabulary #IELTS #DailyEnglish

Rules: B2/C1 level, practical exam vocabulary, Ukrainian translations included.
"""


def _prompt_tricky_pairs(used: list[str]) -> str:
    return f"""Create a "Tricky Pairs" Telegram post for an English learning channel.
Avoid recently used pairs: {used[:20]}

Format (HTML for Telegram):
⚠️ <b>Stop Confusing These!</b>

<b>[WORD 1]</b> vs <b>[WORD 2]</b>

📌 <b>[WORD 1]</b> — [Ukrainian]
[Grammar rule / usage explanation]
✍️ <i>[Example sentence]</i>

📌 <b>[WORD 2]</b> — [Ukrainian]
[Grammar rule / usage explanation]
✍️ <i>[Example sentence]</i>

❌ Common mistake: [typical learner error]
✅ Correct: [correction]

#ExamPrep #TrickyPairs #Grammar #DailyEnglish

Rules: Pick genuinely confusing pairs (e.g. affect/effect, lay/lie, advice/advise).
"""


def _prompt_grammar_quiz(used: list[str]) -> str:
    return f"""Create a "Mini Grammar Quiz" Telegram post for an English learning channel.
Avoid recently used grammar points: {used[:20]}

Format (HTML for Telegram):
🔍 <b>Find the Mistake!</b>

❓ <i>[Sentence with ONE grammatical error — typical IELTS/TOEFL mistake]</i>

🤔 Can you spot it?

✅ <b>Answer:</b>
❌ Wrong: <i>[wrong part]</i>
✅ Correct: <i>[corrected sentence]</i>
📖 <b>Rule:</b> [Explanation in English + Ukrainian translation]

#ExamPrep #GrammarQuiz #Grammar #DailyEnglish

Rules: Error must be subtle (not obvious). Explain the grammar rule clearly.
"""


def _prompt_speaking(used: list[str]) -> str:
    return f"""Create a "Speaking Prompt of the Day" Telegram post for an English learning channel.
Avoid recently used speaking topics: {used[:20]}

Format (HTML for Telegram):
🗣️ <b>Speaking Prompt of the Day</b>

❓ <b>[IELTS/TOEFL Speaking Part 1 or Part 2 question]</b>
<i>[Ukrainian translation of the question]</i>

💡 <b>Useful language:</b>
• Idiom/phrase: <b>[phrase]</b> — [Ukrainian]
• Structure: <b>[grammar structure]</b> — [Ukrainian]

📝 <b>Sample answer (B2/C1):</b>
<i>[3–4 sentence model answer using the idiom/structure above]</i>

#ExamPrep #Speaking #IELTS #TOEFL #DailyEnglish
"""


ROTATION = [
    ("vocab_upgrade",  _prompt_vocab_upgrade),
    ("tricky_pairs",   _prompt_tricky_pairs),
    ("grammar_quiz",   _prompt_grammar_quiz),
    ("speaking",       _prompt_speaking),
]


def post_exam_prep() -> bool:
    logger.info("Generating Exam Prep post…")

    day = get_day_counter("exam_day")
    idx = (day - 1) % len(ROTATION)
    subtype, prompt_fn = ROTATION[idx]

    used = get_history(f"exam_{subtype}")
    prompt = prompt_fn(used)

    content = generate(prompt)

    if not content:
        logger.warning("AI failed — using fallback Exam Prep post.")
        fallback_pool = FALLBACK_EXAM.get(subtype, list(FALLBACK_EXAM.values())[0])
        content = random.choice(fallback_pool)

    success = send_message(content)

    if success:
        increment_day_counter("exam_day")
        add_to_history(f"exam_{subtype}", subtype)

    log_post_published(f"exam_prep_{subtype}", success)
    return success
