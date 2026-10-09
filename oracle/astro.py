"""Астрологические и нумерологические расчёты по дате рождения."""

from dataclasses import dataclass
from datetime import date

# (название, символ, стихия, планета-управитель, (месяц, день) начала знака)
ZODIAC = [
    ("Козерог", "♑", "Земля", "Сатурн", (12, 22)),
    ("Водолей", "♒", "Воздух", "Уран", (1, 20)),
    ("Рыбы", "♓", "Вода", "Нептун", (2, 19)),
    ("Овен", "♈", "Огонь", "Марс", (3, 21)),
    ("Телец", "♉", "Земля", "Венера", (4, 20)),
    ("Близнецы", "♊", "Воздух", "Меркурий", (5, 21)),
    ("Рак", "♋", "Вода", "Луна", (6, 21)),
    ("Лев", "♌", "Огонь", "Солнце", (7, 23)),
    ("Дева", "♍", "Земля", "Меркурий", (8, 23)),
    ("Весы", "♎", "Воздух", "Венера", (9, 23)),
    ("Скорпион", "♏", "Вода", "Плутон", (10, 23)),
    ("Стрелец", "♐", "Огонь", "Юпитер", (11, 22)),
]

CHINESE_ANIMALS = [
    "Крыса", "Бык", "Тигр", "Кролик", "Дракон", "Змея",
    "Лошадь", "Коза", "Обезьяна", "Петух", "Собака", "Свинья",
]
CHINESE_ELEMENTS = ["Металл", "Металл", "Вода", "Вода", "Дерево", "Дерево",
                    "Огонь", "Огонь", "Земля", "Земля"]


@dataclass(frozen=True)
class Profile:
    name: str
    birth_date: date

    @property
    def zodiac(self) -> tuple[str, str, str, str]:
        md = (self.birth_date.month, self.birth_date.day)
        sign = ZODIAC[0]  # Козерог, если дата раньше 20 января или с 22 декабря
        for z in ZODIAC[1:]:
            if md >= z[4]:
                sign = z
        if md >= ZODIAC[0][4]:  # 22–31 декабря
            sign = ZODIAC[0]
        return sign[:4]

    @property
    def chinese_year(self) -> str:
        # Упрощённо по григорианскому году (без учёта даты китайского Нового года).
        y = self.birth_date.year
        return f"{CHINESE_ELEMENTS[y % 10]} {CHINESE_ANIMALS[(y - 4) % 12]}"

    @property
    def life_path(self) -> int:
        """Число жизненного пути: сумма цифр даты рождения (11, 22, 33 не сворачиваются)."""
        n = sum(int(c) for c in self.birth_date.strftime("%Y%m%d"))
        while n > 9 and n not in (11, 22, 33):
            n = sum(int(c) for c in str(n))
        return n

    @property
    def age(self) -> int:
        today = date.today()
        b = self.birth_date
        return today.year - b.year - ((today.month, today.day) < (b.month, b.day))

    def summary(self) -> str:
        name, symbol, element, planet = self.zodiac
        return (
            f"Имя: {self.name}\n"
            f"Дата рождения: {self.birth_date:%d.%m.%Y} (возраст {self.age})\n"
            f"Знак зодиака: {symbol} {name}, стихия {element}, планета {planet}\n"
            f"Восточный гороскоп: {self.chinese_year}\n"
            f"Число жизненного пути: {self.life_path}"
        )


def parse_birth_date(text: str) -> date:
    """Принимает ДД.ММ.ГГГГ, ДД/ММ/ГГГГ, ДД-ММ-ГГГГ или ГГГГ-ММ-ДД."""
    text = text.strip().replace("/", ".").replace("-", ".")
    parts = text.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError("Введите дату в формате ДД.ММ.ГГГГ, например 14.03.1995")
    if len(parts[0]) == 4:
        y, m, d = map(int, parts)
    else:
        d, m, y = map(int, parts)
    try:
        result = date(y, m, d)
    except ValueError as e:
        raise ValueError("Такой даты не существует") from e
    if result > date.today() or result.year < 1900:
        raise ValueError("Дата рождения должна быть между 1900 годом и сегодняшним днём")
    return result
