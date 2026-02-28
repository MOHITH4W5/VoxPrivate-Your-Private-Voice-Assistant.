"""
tests/test_config.py
Unit tests for the config loader.
"""

import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.config import Config


SAMPLE_YAML = """
audio:
  sample_rate: 16000
  chunk_size: 1024
model:
  speech_recognition: tiny
  gpu_acceleration: false
tts:
  rate: 175
  volume: 1.0
"""


def test_config_load():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(SAMPLE_YAML)
        path = f.name
    cfg = Config.from_file(path)
    assert cfg.get("audio", "sample_rate") == 16000
    assert cfg.get("model", "speech_recognition") == "tiny"
    assert cfg.get("tts", "rate") == 175
    os.unlink(path)

def test_config_missing_key_default():
    cfg = Config({})
    assert cfg.get("nonexistent", "key", default="fallback") == "fallback"


if __name__ == "__main__":
    for t in [test_config_load, test_config_missing_key_default]:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}")
