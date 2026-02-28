"""
tests/test_intent.py
Unit tests for the intent classifier.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.intent_classifier import classify_intent


def test_time_intent():
    intent, _ = classify_intent("What's the time?")
    assert intent == "time", f"Expected 'time', got '{intent}'"

def test_date_intent():
    intent, _ = classify_intent("What's today's date?")
    assert intent == "date", f"Expected 'date', got '{intent}'"

def test_screenshot_intent():
    intent, _ = classify_intent("Take a screenshot")
    assert intent == "screenshot"

def test_open_terminal_intent():
    intent, _ = classify_intent("Open terminal")
    assert intent == "open_terminal"

def test_create_file_intent():
    intent, meta = classify_intent("Create a file named hello.txt")
    assert intent == "create_file"
    assert meta.get("filename") == "hello.txt"

def test_unknown_intent():
    intent, _ = classify_intent("xyzzy blorg fnord")
    assert intent == "unknown"

def test_help_intent():
    intent, _ = classify_intent("What can you do?")
    assert intent == "help"

def test_stop_intent():
    intent, _ = classify_intent("Goodbye")
    assert intent == "stop"

def test_volume_up():
    intent, _ = classify_intent("Volume up")
    assert intent == "volume_up"

def test_open_browser():
    intent, _ = classify_intent("Open browser")
    assert intent == "open_browser"


if __name__ == "__main__":
    tests = [
        test_time_intent, test_date_intent, test_screenshot_intent,
        test_open_terminal_intent, test_create_file_intent, test_unknown_intent,
        test_help_intent, test_stop_intent, test_volume_up, test_open_browser,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} tests passed.")
