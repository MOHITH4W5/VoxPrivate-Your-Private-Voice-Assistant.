"""
src/models/intent_classifier.py
Lightweight keyword-based intent classifier.
No ML model download required — fast and fully offline.
"""

import re
from typing import Optional, Tuple


# Intent → list of trigger phrases/keywords
INTENT_PATTERNS = {
    "time": [
        r"\btime\b", r"\bwhat time\b", r"\bcurrent time\b",
        r"\bwhat('s| is) the time\b",
    ],
    "date": [
        r"\bdate\b", r"\btoday\b", r"\bwhat day\b",
        r"\bwhat('s| is) today\b", r"\bwhat('s| is) the date\b",
    ],
    "open_terminal": [
        r"\bopen (terminal|cmd|command prompt|console|shell)\b",
        r"\blaunch (terminal|cmd|console)\b",
        r"\bstart (terminal|cmd|console)\b",
    ],
    "screenshot": [
        r"\b(take|capture|grab) (a )?screenshot\b",
        r"\bscreenshot\b",
    ],
    "create_file": [
        r"\bcreate (a )?file\b",
        r"\bmake (a )?file\b",
        r"\bnew file\b",
    ],
    "open_browser": [
        r"\bopen (browser|chrome|firefox|edge|internet)\b",
        r"\blaunch (browser|chrome|firefox|edge)\b",
        r"\bstart (browser|chrome|firefox|edge)\b",
    ],
    "play_music": [
        r"\bplay (some )?music\b",
        r"\bopen music\b",
        r"\blaunch music (player)?\b",
        r"\bplay (songs?|audio)\b",
    ],
    "volume_up": [
        r"\bvolume up\b", r"\bincrease volume\b", r"\blouder\b",
        r"\bturn (it )?up\b",
    ],
    "volume_down": [
        r"\bvolume down\b", r"\bdecrease volume\b", r"\bquieter\b",
        r"\bturn (it )?down\b",
    ],
    "mute": [
        r"\bmute\b", r"\bsilence\b", r"\bturn off (the )?sound\b",
    ],
    "shutdown": [
        r"\bshutdown\b", r"\bshut down\b", r"\bpower off\b",
        r"\bturn off (the )?(computer|pc|system)\b",
    ],
    "restart": [
        r"\brestart\b", r"\breboot\b",
        r"\brestart (the )?(computer|pc|system)\b",
    ],
    "sleep": [
        r"\bsleep\b", r"\bhibernate\b",
        r"\bput (the )?(computer|pc|system) to sleep\b",
    ],
    "calculator": [
        r"\bopen (calculator|calc)\b",
        r"\blaunch (calculator|calc)\b",
    ],
    "notepad": [
        r"\bopen (notepad|text editor|notes)\b",
        r"\blaunch (notepad|text editor|notes)\b",
    ],
    "help": [
        r"\bhelp\b", r"\bwhat can you do\b", r"\bcommands\b",
        r"\bwhat (do )?you know\b",
    ],
    "stop": [
        r"\bstop\b", r"\bexit\b", r"\bquit\b", r"\bbye\b",
        r"\bgoodbye\b", r"\bclose\b",
    ],
}

# Extract file name from "create a file named foo.txt"
FILE_NAME_PATTERN = re.compile(
    r"(?:named?|called?|with name)\s+([^\s]+)", re.IGNORECASE
)


def classify_intent(text: str) -> Tuple[str, dict]:
    """
    Classify intent from transcribed text.

    Returns:
        (intent_name, metadata_dict)
        e.g. ("create_file", {"filename": "test.txt"})
        or   ("unknown", {})
    """
    text_lower = text.lower().strip()
    metadata = {}

    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                # Extract extra metadata for certain intents
                if intent == "create_file":
                    match = FILE_NAME_PATTERN.search(text)
                    metadata["filename"] = match.group(1) if match else "new_file.txt"
                return intent, metadata

    return "unknown", {}
