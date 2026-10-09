"""Простые предсказания без ИИ — когда ключ не задан или нет интернета."""

import hashlib
import random
from datetime import date

from .astro import Profile
from .tarot import DrawnCard, describe

MOODS = ["день подходит для смелых шагов", "лучше не спешить и присмотреться",
         "энергия на подъёме — используйте её", "хорошее время закончить старые дела",
         "интуиция сегодня особенно точна", "удача любит тех, кто проявляет инициативу"]
LOVE = ["искренний разговор сблизит вас", "не требуйте слишком многого от близких",
        "возможно приятное знакомство", "проявите заботу первым"]
WORK = ["новая идея может принести доход", "избегайте импульсивных трат",
        "завершите то, что давно откладывали", "договорённости сегодня прочны"]
ADVICE = ["выделите время для себя", "прислушайтесь к первому впечатлению",
          "сделайте одно доброе дело", "запишите свои цели на бумаге"]


def horoscope(profile: Profile, day: date | None = None) -> str:
    day = day or date.today()
    seed = hashlib.sha256(f"{profile.name}|{profile.birth_date}|{day}".encode()).hexdigest()
    rng = random.Random(int(seed, 16))
    sign, symbol, element, planet = profile.zodiac
    return (
        f"{symbol} {profile.name}, гороскоп для знака {sign} на {day:%d.%m.%Y}\n\n"
        f"Общий настрой: {rng.choice(MOODS)}. Стихия {element} и планета {planet} задают тон дня.\n"
        f"Любовь: {rng.choice(LOVE)}.\n"
        f"Работа и деньги: {rng.choice(WORK)}.\n"
        f"Совет: {rng.choice(ADVICE)}.\n"
        f"Счастливое число: {rng.randint(1, 9) + profile.life_path}"
    )


def tarot_reading(profile: Profile, spread_name: str, cards: list[DrawnCard]) -> str:
    return f"🃏 {profile.name}, ваш расклад «{spread_name}»:\n\n{describe(cards)}"
