"""Подключение к ИИ (Claude) для толкования раскладов и гороскопов."""

from collections.abc import Callable
from datetime import date

import anthropic

from . import config
from .astro import Profile
from .tarot import DrawnCard, describe

SYSTEM_PROMPT = """Ты — Оракул, тёплый и мудрый таролог и астролог. Отвечай по-русски.

Как отвечать:
- Обращайся к человеку по имени, учитывай его знак зодиака, стихию, восточный гороскоп и число жизненного пути.
- Толкуй карты Таро в связке друг с другом и с позицией в раскладе, а не по отдельности.
- Пиши образно, но конкретно: что это значит для человека сегодня и какой практический шаг можно сделать.
- Объём — 150–300 слов, если не просят иначе. Используй короткие абзацы, можно эмодзи по теме.
- Не запугивай и не делай категоричных предсказаний о смерти, болезнях или катастрофах.
- Если вопрос касается здоровья, денег или права, мягко добавь, что важные решения стоит обсуждать со специалистом.
- Это развлекательное и вдохновляющее предсказание — подавай его как подсказку, а не как приговор."""

OnText = Callable[[str], None]


class OracleAI:
    def __init__(self) -> None:
        self.client = anthropic.Anthropic()

    def ask(self, messages: list[dict], on_text: OnText | None = None) -> tuple[str, list]:
        """Отправляет диалог в Claude. Возвращает (текст ответа, блоки ответа для истории)."""
        with self.client.beta.messages.stream(
            model=config.MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            messages=messages,
            output_config={"effort": config.EFFORT},
            # Если модель откажется отвечать, API сам переадресует запрос подходящей модели.
            betas=["server-side-fallback-2026-07-01"],
            extra_body={"fallbacks": "default"},
        ) as stream:
            for text in stream.text_stream:
                if on_text:
                    on_text(text)
            final = stream.get_final_message()

        if final.stop_reason == "refusal":
            return "🔮 Карты молчат на этот вопрос. Попробуйте сформулировать его иначе.", []
        text = "".join(b.text for b in final.content if b.type == "text")
        # Блоки ответа возвращаются в историю без изменений — так диалог остаётся корректным.
        return text, [b.model_dump(mode="json", exclude_none=True) for b in final.content]


def profile_block(profile: Profile) -> str:
    return f"Данные человека:\n{profile.summary()}\nСегодня: {date.today():%d.%m.%Y}"


def horoscope_prompt(profile: Profile, period: str = "сегодня") -> str:
    return (
        f"{profile_block(profile)}\n\n"
        f"Составь персональный гороскоп на {period}: общий настрой, любовь и отношения, "
        f"работа и деньги, здоровье и энергия, совет дня и счастливое число."
    )


def tarot_prompt(profile: Profile, spread_name: str, cards: list[DrawnCard], question: str = "") -> str:
    q = f"\nВопрос человека: «{question}»" if question else ""
    return (
        f"{profile_block(profile)}{q}\n\n"
        f"Расклад «{spread_name}». Выпали карты:\n{describe(cards)}\n\n"
        f"Дай толкование расклада для этого человека."
    )


def friendly_error(err: Exception) -> str:
    if isinstance(err, anthropic.AuthenticationError):
        return "Ключ ИИ не подошёл. Проверьте ANTHROPIC_API_KEY в файле .env."
    if isinstance(err, anthropic.PermissionDeniedError):
        return "У этого ключа нет доступа к выбранной модели. Проверьте ORACLE_MODEL или аккаунт."
    if isinstance(err, anthropic.RateLimitError):
        return "ИИ сейчас перегружен запросами. Подождите минуту и попробуйте снова."
    if isinstance(err, anthropic.APIConnectionError):
        return "Нет связи с ИИ. Проверьте интернет."
    if isinstance(err, anthropic.APIStatusError):
        return f"ИИ вернул ошибку {err.status_code}: {err.message}"
    return f"Непредвиденная ошибка: {err}"
