from datetime import datetime

ALLOWED_CURRENCIES = {"UAH", "USD", "EUR"}


def read_int(prompt: str) -> int:
    while True:
        s = input(prompt).strip()
        if s.isdigit():
            return int(s)
        print("Введіть ціле число.")


def read_amount(prompt: str) -> float:
    while True:
        s = input(prompt).strip().lower()
        s = s.replace("грн", "").replace(" ", "").replace(",", ".")
        try:
            value = float(s)
            if value <= 0:
                print(" Сума має бути більшою за 0.")
                continue
            return value
        except ValueError:
            print(" Введіть число (наприклад 125.50 або 3400 грн).")


def read_optional_amount(prompt: str) -> float | None:
    s = input(prompt).strip().lower()
    if s == "":
        return None
    s = s.replace("грн", "").replace(" ", "").replace(",", ".")
    try:
        value = float(s)
        if value <= 0:
            print(" Сума має бути більшою за 0.")
            return read_optional_amount(prompt)
        return value
    except ValueError:
        print(" Введіть число або Enter щоб не змінювати.")
        return read_optional_amount(prompt)


def read_date(prompt: str = "Дата (YYYY-MM-DD або DD.MM.YYYY): ") -> str:
    """
    Ввід: YYYY-MM-DD або DD.MM.YYYY
    Вихід: YYYY-MM-DD (уніфіковано для PostgreSQL)
    """
    while True:
        s = input(prompt).strip()
        for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
            try:
                dt = datetime.strptime(s, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass
        print(" Невірний формат. Введіть YYYY-MM-DD (2026-02-25) або DD.MM.YYYY (25.02.2026).")


def read_optional_date(prompt: str = "Нова дата (Enter = не змінювати, YYYY-MM-DD або DD.MM.YYYY): ") -> str | None:
    s = input(prompt).strip()
    if s == "":
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    print(" Невірний формат. Введіть YYYY-MM-DD або DD.MM.YYYY. Або Enter щоб не змінювати.")
    return read_optional_date(prompt)


def read_currency(prompt: str = "Валюта (Enter = UAH, UAH/USD/EUR): ") -> str:
    while True:
        s = input(prompt).strip().upper()
        if s == "":
            return "UAH"
        if s in ALLOWED_CURRENCIES:
            return s
        print(" Невірна валюта. Дозволено: UAH, USD, EUR. Або Enter для UAH.")


def read_optional_currency(prompt: str = "Валюта (Enter = не змінювати, UAH/USD/EUR): ") -> str | None:
    s = input(prompt).strip().upper()
    if s == "":
        return None
    if s in ALLOWED_CURRENCIES:
        return s
    print(" Невірна валюта. Дозволено: UAH, USD, EUR. Або Enter щоб не змінювати.")
    return read_optional_currency(prompt)

