from datetime import date

import pytest

from oracle import offline
from oracle.astro import Profile, parse_birth_date
from oracle.tarot import DECK, SPREADS, card_of_the_day, draw


@pytest.mark.parametrize("birth, sign", [
    (date(1995, 3, 14), "Рыбы"),
    (date(1990, 12, 25), "Козерог"),
    (date(1990, 1, 19), "Козерог"),
    (date(1990, 1, 20), "Водолей"),
    (date(2000, 7, 23), "Лев"),
    (date(1999, 3, 21), "Овен"),
])
def test_zodiac(birth, sign):
    assert Profile("A", birth).zodiac[0] == sign


def test_chinese_and_life_path():
    p = Profile("A", date(1995, 3, 14))
    assert p.chinese_year == "Дерево Свинья"
    assert p.life_path == 5  # 1+4+0+3+1+9+9+5 = 32 -> 5
    assert Profile("A", date(1990, 1, 20)).life_path == 22


@pytest.mark.parametrize("text, expected", [
    ("14.03.1995", date(1995, 3, 14)),
    ("14/03/1995", date(1995, 3, 14)),
    ("1995-03-14", date(1995, 3, 14)),
])
def test_parse_birth_date(text, expected):
    assert parse_birth_date(text) == expected


@pytest.mark.parametrize("text", ["31.02.1990", "abc", "01.01.2999", "1.1"])
def test_parse_birth_date_invalid(text):
    with pytest.raises(ValueError):
        parse_birth_date(text)


def test_deck_and_spreads():
    assert len(DECK) == 78
    assert len({c.name for c in DECK}) == 78
    for spread, positions in SPREADS.items():
        cards = draw(spread)
        assert [c.position for c in cards] == positions
        assert len({c.card.name for c in cards}) == len(cards)


def test_card_of_the_day_is_stable():
    d = date(2026, 10, 9)
    a = card_of_the_day("Анна", date(1995, 3, 14), d)
    assert a == card_of_the_day(" анна", date(1995, 3, 14), d)


def test_offline_horoscope_mentions_sign():
    text = offline.horoscope(Profile("Анна", date(1995, 3, 14)))
    assert "Анна" in text and "Рыбы" in text
