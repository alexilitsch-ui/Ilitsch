"""Точка входа: `python main.py` — консоль, `python main.py telegram` — Telegram-бот."""

import sys

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "telegram":
        from oracle.telegram_bot import main
    else:
        from oracle.cli import main
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nДо встречи! 🌙")
