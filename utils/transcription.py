"""
Transcription helper — converts English words to IPA using eng_to_ipa.
If a word is not found in the dictionary, returns an empty string.
"""
import logging
import re

try:
    import eng_to_ipa as ipa
    IPA_AVAILABLE = True
except ImportError:
    IPA_AVAILABLE = False
    logging.warning("eng_to_ipa not installed — transcription disabled.")

logger = logging.getLogger(__name__)


def get_ipa(word: str) -> str:
    """
    Return IPA transcription for a single word, wrapped in slashes.
    e.g.  "example"  →  "/ɪɡˈzæmpəl/"
    Returns "" if unavailable.
    """
    if not IPA_AVAILABLE:
        return ""
    word_clean = re.sub(r"[^a-zA-Z'-]", "", word).lower()
    result = ipa.convert(word_clean)
    # eng_to_ipa marks unknown words with "*"
    if "*" in result or not result:
        return ""
    return f"/{result}/"


def get_ipa_multi(text: str) -> str:
    """
    Return IPA for a multi-word phrase (word by word, joined with spaces).
    e.g.  "break a leg"  →  "/breɪk ə lɛɡ/"
    """
    if not IPA_AVAILABLE:
        return ""
    words = text.split()
    parts = []
    for w in words:
        clean = re.sub(r"[^a-zA-Z'-]", "", w).lower()
        res = ipa.convert(clean)
        if "*" in res or not res:
            parts.append(w)  # keep original if unknown
        else:
            parts.append(res)
    return "/" + " ".join(parts) + "/"
