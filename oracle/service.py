"""Общая логика бота: выбирает ИИ или офлайн-режим. Используется консолью и Telegram."""

from . import config, offline
from .ai import OracleAI, friendly_error, horoscope_prompt, profile_block, tarot_prompt
from .astro import Profile
from .tarot import DrawnCard, card_of_the_day, draw

SPREAD_NAMES = {
    "day": "Карта дня",
    "three": "Прошлое — Настоящее — Будущее",
    "love": "Любовный расклад",
    "question": "Ответ на вопрос",
}


class Oracle:
    def __init__(self, profile: Profile) -> None:
        self.profile = profile
        self.ai = OracleAI() if config.ai_available() else None
        self.chat_history: list[dict] = []

    @property
    def uses_ai(self) -> bool:
        return self.ai is not None

    def _ask_ai(self, prompt: str, fallback: str, on_text=None) -> str:
        if not self.ai:
            return fallback
        try:
            text, _ = self.ai.ask([{"role": "user", "content": prompt}], on_text)
            return text
        except Exception as err:  # показываем офлайн-ответ, если ИИ недоступен
            return f"⚠️ {friendly_error(err)}\n\n{fallback}"

    def horoscope(self, on_text=None) -> str:
        return self._ask_ai(horoscope_prompt(self.profile), offline.horoscope(self.profile), on_text)

    def tarot(self, spread: str, question: str = "", on_text=None) -> tuple[list[DrawnCard], str]:
        if spread == "day":
            cards = [card_of_the_day(self.profile.name, self.profile.birth_date)]
        else:
            cards = draw(spread)
        name = SPREAD_NAMES[spread]
        fallback = offline.tarot_reading(self.profile, name, cards)
        text = self._ask_ai(tarot_prompt(self.profile, name, cards, question), fallback, on_text)
        return cards, text

    def chat(self, message: str, on_text=None) -> str:
        """Свободный разговор с Оракулом с памятью в пределах сеанса."""
        if not self.ai:
            return "Свободный чат доступен только с ИИ. Добавьте ANTHROPIC_API_KEY в файл .env."
        if not self.chat_history:
            message = f"{profile_block(self.profile)}\n\n{message}"
        self.chat_history.append({"role": "user", "content": message})
        try:
            text, content = self.ai.ask(self.chat_history, on_text)
        except Exception as err:
            self.chat_history.pop()
            return f"⚠️ {friendly_error(err)}"
        if content:
            self.chat_history.append({"role": "assistant", "content": content})
        else:  # отказ модели — убираем вопрос, чтобы история осталась корректной
            self.chat_history.pop()
        return text
