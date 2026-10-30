"""
This project scrapes websites only. Telegram is Ollaa-Telegram's job (owner, 30 October 2026),
so no Telegram source or Telegram code may come back here.
"""
import pathlib

from source_registry import SOURCE_REGISTRY

PROJECT_DIR = pathlib.Path(__file__).resolve().parent.parent
SKIP_DIRS = {"venv", ".venv", "site-packages", "__pycache__", ".pytest_cache"}
TELEGRAM_WORDS = ("telegram", "t.me/", "telethon", "pyrogram", "tgme_")


def test_no_telegram_sources():
    for key, source in SOURCE_REGISTRY.items():
        text = f"{key} {source.get('name', '')} {source.get('url', '')} {source.get('category', '')}".lower()
        assert not any(word in text for word in TELEGRAM_WORDS), f"Telegram source in registry: {key}"


def test_no_telegram_code():
    for path in PROJECT_DIR.rglob("*.py"):
        if path.name == "test_no_telegram.py" or SKIP_DIRS & set(path.parts):
            continue
        text = path.read_text(encoding="utf-8").lower()
        found = [word for word in TELEGRAM_WORDS if word in text]
        assert not found, f"Telegram code in {path.relative_to(PROJECT_DIR)}: {found}"
