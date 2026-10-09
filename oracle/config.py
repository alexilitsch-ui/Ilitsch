"""Настройки из переменных окружения и файла .env рядом с проектом."""

import os
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def load_env() -> None:
    """Подхватывает KEY=VALUE из .env, не перезаписывая уже заданные переменные."""
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env()

MODEL = os.environ.get("ORACLE_MODEL", "claude-opus-5-5")
EFFORT = os.environ.get("ORACLE_EFFORT", "medium")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")


def ai_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))
