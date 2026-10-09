"""Консольный режим: Оракул прямо на вашем компьютере."""

import sys

from . import config
from .astro import Profile, parse_birth_date
from .service import Oracle

MENU = """
╔══════════════════════════════════════╗
  1 — Гороскоп на сегодня
  2 — Карта дня
  3 — Расклад: прошлое, настоящее, будущее
  4 — Любовный расклад
  5 — Задать вопрос картам
  6 — Поговорить с Оракулом (чат с ИИ)
  7 — Мой астропрофиль
  0 — Выход
╚══════════════════════════════════════╝"""


def stream_print(text: str) -> None:
    print(text, end="", flush=True)


def ask_profile() -> Profile:
    name = ""
    while not name:
        name = input("Как вас зовут? ").strip()
    while True:
        try:
            birth = parse_birth_date(input("Дата рождения (ДД.ММ.ГГГГ): "))
            return Profile(name, birth)
        except ValueError as e:
            print(f"  {e}")


def show(oracle: Oracle, produce) -> None:
    """Печатает ответ: при ИИ — по мере генерации, без ИИ — целиком."""
    print()
    if oracle.uses_ai:
        print("🔮 Оракул думает...\n")
        streamed = []
        result = produce(lambda t: (streamed.append(t), stream_print(t)))
        if not streamed:  # ошибка или отказ — текст не шёл потоком
            print(result)
        print()
    else:
        print(produce(None))


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("✨ Добро пожаловать к Оракулу — Таро и гороскоп ✨")
    if config.ai_available():
        print(f"ИИ подключён (модель {config.MODEL}).")
    else:
        print("ИИ не подключён — работаю в простом режиме. Чтобы подключить, см. README.")

    oracle = Oracle(ask_profile())
    sign, symbol, *_ = oracle.profile.zodiac
    print(f"\nРад знакомству, {oracle.profile.name}! Ваш знак — {symbol} {sign}.")

    while True:
        print(MENU)
        choice = input("Выберите пункт: ").strip()
        if choice == "0":
            print("Да хранят вас звёзды! 🌙")
            return
        if choice == "1":
            show(oracle, lambda cb: oracle.horoscope(cb))
        elif choice in ("2", "3", "4", "5"):
            spread = {"2": "day", "3": "three", "4": "love", "5": "question"}[choice]
            question = input("Ваш вопрос: ").strip() if spread == "question" else ""
            cards_box = {}

            def produce(cb, spread=spread, question=question):
                cards, text = oracle.tarot(spread, question, cb)
                cards_box["cards"] = cards
                return text

            show(oracle, produce)
            if oracle.uses_ai:
                print("\nВыпавшие карты:")
                for c in cards_box["cards"]:
                    print(f"  🃏 {c.position}: {c.title}")
        elif choice == "6":
            print("Пишите вопросы Оракулу. Пустая строка — назад в меню.")
            while msg := input("\nВы: ").strip():
                print("Оракул: ", end="")
                show(oracle, lambda cb, m=msg: oracle.chat(m, cb))
        elif choice == "7":
            print("\n" + oracle.profile.summary())
        else:
            print("Нет такого пункта.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nДо встречи! 🌙")
