# reports.py
import os
import csv
from db import get_conn
from utils import read_date
from categories import list_categories, get_category_name


# ---------- helpers ----------
def _normalize_period(date_from: str, date_to: str) -> tuple[str, str]:
    """Якщо дати переплутані місцями — міняємо."""
    if date_from > date_to:
        print(" Дата ВІД більша за Дата ДО. Міняю місцями.")
        return date_to, date_from
    return date_from, date_to


# ---------- Reports меню ----------
def reports_menu():
    while True:
        print("\n=== Звіти ===")
        print("1. Витрати за період")
        print("2. Фільтрація за назвою витрати")
        print("3. Витрати по категорії (ID)")
        print("4. Максимальна витрата у кожній категорії")
        print("5. Максимальна витрата у періоді")
        print("6. Мінімальна витрата у кожній категорії")
        print("7. Мінімальна витрата у періоді")
        print("8. Підсумки по категоріях за період (підменю)")
        print("9. Експорт витрат за період у CSV")
        print("0. Назад")

        choice = input("Ваш вибір: ").strip()

        if choice == "1":
            report_expenses_by_period()
        elif choice == "2":
            report_filter_by_title()
        elif choice == "3":
            report_expenses_by_category_id()
        elif choice == "4":
            report_max_expense_per_category()
        elif choice == "5":
            report_max_expense_in_period()
        elif choice == "6":
            report_min_expense_per_category()
        elif choice == "7":
            report_min_expense_in_period()
        elif choice == "8":
            summary_menu()
        elif choice == "9":
            export_expenses_by_period_to_csv()
        elif choice == "0":
            return
        else:
            print(" Невірний вибір.")


def summary_menu():
    while True:
        print("\n=== Підсумки по категоріях за період ===")
        print("1. Сума по кожній категорії за період (окремо по валюті)")
        print("2. ТОП категорія за період (де витрат найбільше, окремо по валюті)")
        print("3. Середні витрати на день за період (окремо по валюті)")
        print("0. Назад")

        choice = input("Ваш вибір: ").strip()

        if choice == "1":
            report_sum_by_category_in_period()
        elif choice == "2":
            report_top_category_in_period()
        elif choice == "3":
            report_avg_per_day_in_period()
        elif choice == "0":
            return
        else:
            print(" Невірний вибір.")


# ---------- 1) Витрати за період ----------
def report_expenses_by_period():
    print("\n--- Звіт: витрати за період ---")
    date_from = read_date("Дата ВІД (YYYY-MM-DD або DD.MM.YYYY): ")
    date_to = read_date("Дата ДО (YYYY-MM-DD або DD.MM.YYYY): ")
    date_from, date_to = _normalize_period(date_from, date_to)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    e.expense_date,
                    c.name AS category,
                    e.title,
                    e.amount,
                    e.currency,
                    COALESCE(e.description, '')
                FROM expenses e
                JOIN categories c ON c.id = e.category_id
                WHERE e.expense_date BETWEEN %s AND %s
                ORDER BY e.expense_date, e.id;
            """, (date_from, date_to))
            rows = cur.fetchall()

        if not rows:
            print("За цей період витрат немає.")
            return

        print("\nДата | Категорія | Назва | Сума | Валюта | Опис")
        print("-" * 100)
        for d, cat, title, amount, curr, desc in rows:
            tail = f" | {desc}" if desc else ""
            print(f"{d} | {cat} | {title} | {amount} | {curr}{tail}")
        print()
    finally:
        conn.close()


# ---------- 2) Фільтрація за назвою витрати (title) ----------
def report_filter_by_title():
    print("\n--- Фільтрація витрат за назвою витрати (title) ---")
    text = input("Введіть назву витрати або її частину: ").strip()

    if not text:
        print(" Текст не може бути порожнім")
        return

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    e.expense_date,
                    c.name AS category,
                    e.title,
                    e.amount,
                    e.currency,
                    COALESCE(e.description, '')
                FROM expenses e
                JOIN categories c ON c.id = e.category_id
                WHERE LOWER(e.title) LIKE LOWER(%s)
                ORDER BY e.expense_date, e.id;
            """, (f"%{text}%",))
            rows = cur.fetchall()

        if not rows:
            print("Нічого не знайдено.")
            return

        print("\nДата | Категорія | Назва | Сума | Валюта | Опис")
        print("-" * 100)
        for d, cat, title, amount, curr, desc in rows:
            tail = f" | {desc}" if desc else ""
            print(f"{d} | {cat} | {title} | {amount} | {curr}{tail}")
        print()
    finally:
        conn.close()


# ---------- 3) Витрати по конкретній категорії (WHERE e.category_id = %s) ----------
def report_expenses_by_category_id():
    print("\n--- Звіт: витрати по конкретній категорії (category_id) ---")
    list_categories()

    raw = input("Введіть ID категорії: ").strip()
    if not raw.isdigit():
        print(" ID має бути числом.")
        return

    category_id = int(raw)
    if get_category_name(category_id) is None:
        print(" Категорію з таким ID не знайдено.")
        return

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    e.id,
                    e.expense_date,
                    e.title,
                    e.amount,
                    e.currency,
                    COALESCE(e.description, '')
                FROM expenses e
                WHERE e.category_id = %s
                ORDER BY e.expense_date, e.id;
            """, (category_id,))
            rows = cur.fetchall()

        if not rows:
            print("У цій категорії витрат немає.")
            return

        print("\nID | Дата | Назва | Сума | Валюта | Опис")
        print("-" * 100)
        for eid, dt, title, amount, curr, desc in rows:
            tail = f" | {desc}" if desc else ""
            print(f"{eid} | {dt} | {title} | {amount} | {curr}{tail}")
        print()
    finally:
        conn.close()


# ---------- 4) Максимальна витрата у кожній категорії (DISTINCT ON) ----------
def report_max_expense_per_category():
    print("\n--- Звіт: максимальна витрата у кожній категорії (окремо по валюті) ---")

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT ON (c.id, e.currency)
                    c.name AS category,
                    e.currency,
                    e.id,
                    e.expense_date,
                    e.title,
                    e.amount,
                    COALESCE(e.description, '') AS description
                FROM categories c
                JOIN expenses e ON e.category_id = c.id
                ORDER BY c.id, e.currency, e.amount DESC, e.expense_date DESC, e.id DESC;
            """)
            rows = cur.fetchall()

        if not rows:
            print("Витрат поки що немає.")
            return

        print("\nКатегорія | Валюта | ID | Дата | Назва | Сума | Опис")
        print("-" * 120)
        for cat, curr, eid, dt, title, amount, desc in rows:
            tail = f" | {desc}" if desc else ""
            print(f"{cat} | {curr} | {eid} | {dt} | {title} | {amount}{tail}")
        print()
    finally:
        conn.close()


# ---------- 5) Максимальна витрата за вибраний період ----------
def report_max_expense_in_period():
    print("\n--- Звіт: максимальна витрата у періоді (окремо по валюті) ---")
    date_from = read_date("Дата ВІД (YYYY-MM-DD або DD.MM.YYYY): ")
    date_to = read_date("Дата ДО (YYYY-MM-DD або DD.MM.YYYY): ")
    date_from, date_to = _normalize_period(date_from, date_to)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT ON (e.currency)
                    e.currency,
                    e.id,
                    e.expense_date,
                    c.name AS category,
                    e.title,
                    e.amount,
                    COALESCE(e.description, '') AS description
                FROM expenses e
                JOIN categories c ON c.id = e.category_id
                WHERE e.expense_date BETWEEN %s AND %s
                ORDER BY e.currency, e.amount DESC, e.expense_date DESC, e.id DESC;
            """, (date_from, date_to))
            rows = cur.fetchall()

        if not rows:
            print("За цей період витрат немає.")
            return

        print("\nMAX витрата за період (окремо по валюті):")
        for curr, eid, dt, cat, title, amount, desc in rows:
            tail = f" | {desc}" if desc else ""
            print(f"{curr}: ID={eid} | {dt} | {cat} | {title} | {amount} {curr}{tail}")
        print()
    finally:
        conn.close()


# ---------- 6) Мінімальна витрата у кожній категорії ----------
def report_min_expense_per_category():
    print("\n--- Звіт: мінімальна витрата у кожній категорії (окремо по валюті) ---")

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT ON (c.id, e.currency)
                    c.name AS category,
                    e.currency,
                    e.id,
                    e.expense_date,
                    e.title,
                    e.amount,
                    COALESCE(e.description, '') AS description
                FROM categories c
                JOIN expenses e ON e.category_id = c.id
                ORDER BY c.id, e.currency, e.amount ASC, e.expense_date DESC, e.id DESC;
            """)
            rows = cur.fetchall()

        if not rows:
            print("Витрат поки що немає.")
            return

        print("\nКатегорія | Валюта | ID | Дата | Назва | Сума | Опис")
        print("-" * 120)
        for cat, curr, eid, dt, title, amount, desc in rows:
            tail = f" | {desc}" if desc else ""
            print(f"{cat} | {curr} | {eid} | {dt} | {title} | {amount}{tail}")
        print()
    finally:
        conn.close()


# ---------- 7) Мінімальна витрата за вибраний період ----------
def report_min_expense_in_period():
    print("\n--- Звіт: мінімальна витрата у періоді (окремо по валюті) ---")
    date_from = read_date("Дата ВІД (YYYY-MM-DD або DD.MM.YYYY): ")
    date_to = read_date("Дата ДО (YYYY-MM-DD або DD.MM.YYYY): ")
    date_from, date_to = _normalize_period(date_from, date_to)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT ON (e.currency)
                    e.currency,
                    e.id,
                    e.expense_date,
                    c.name AS category,
                    e.title,
                    e.amount,
                    COALESCE(e.description, '') AS description
                FROM expenses e
                JOIN categories c ON c.id = e.category_id
                WHERE e.expense_date BETWEEN %s AND %s
                ORDER BY e.currency, e.amount ASC, e.expense_date DESC, e.id DESC;
            """, (date_from, date_to))
            rows = cur.fetchall()

        if not rows:
            print("За цей період витрат немає.")
            return

        print("\nMIN витрата за період (окремо по валюті):")
        for curr, eid, dt, cat, title, amount, desc in rows:
            tail = f" | {desc}" if desc else ""
            print(f"{curr}: ID={eid} | {dt} | {cat} | {title} | {amount} {curr}{tail}")
        print()
    finally:
        conn.close()


# ---------- 8.1) Сума по кожній категорії за період ----------
def report_sum_by_category_in_period():
    print("\n--- Підсумки: сума по кожній категорії за період (окремо по валюті) ---")
    date_from = read_date("Дата ВІД (YYYY-MM-DD або DD.MM.YYYY): ")
    date_to = read_date("Дата ДО (YYYY-MM-DD або DD.MM.YYYY): ")
    date_from, date_to = _normalize_period(date_from, date_to)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    c.name AS category,
                    e.currency,
                    SUM(e.amount) AS total_amount
                FROM expenses e
                JOIN categories c ON c.id = e.category_id
                WHERE e.expense_date BETWEEN %s AND %s
                GROUP BY c.name, e.currency
                ORDER BY c.name, e.currency;
            """, (date_from, date_to))
            rows = cur.fetchall()

        if not rows:
            print("За цей період витрат немає.")
            return

        print("\nКатегорія | Валюта | Загальна сума")
        print("-" * 60)
        for name, curr, total in rows:
            print(f"{name} | {curr} | {total}")
        print()
    finally:
        conn.close()


# ---------- 8.2) ТОП категорія за період ----------
def report_top_category_in_period():
    print("\n--- Підсумки: ТОП категорія за період (окремо по валюті) ---")
    date_from = read_date("Дата ВІД (YYYY-MM-DD або DD.MM.YYYY): ")
    date_to = read_date("Дата ДО (YYYY-MM-DD або DD.MM.YYYY): ")
    date_from, date_to = _normalize_period(date_from, date_to)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                WITH sums AS (
                    SELECT
                        c.name AS category,
                        e.currency,
                        SUM(e.amount) AS total_amount
                    FROM expenses e
                    JOIN categories c ON c.id = e.category_id
                    WHERE e.expense_date BETWEEN %s AND %s
                    GROUP BY c.name, e.currency
                )
                SELECT DISTINCT ON (currency)
                    currency, category, total_amount
                FROM sums
                ORDER BY currency, total_amount DESC;
            """, (date_from, date_to))
            rows = cur.fetchall()

        if not rows:
            print("За цей період витрат немає.")
            return

        print("\nВалюта | ТОП категорія | Сума")
        print("-" * 55)
        for curr, cat, total in rows:
            print(f"{curr} | {cat} | {total}")
        print()
    finally:
        conn.close()


# ---------- 8.3) Середні витрати на день за період ----------
def report_avg_per_day_in_period():
    print("\n--- Підсумки: середні витрати на день за період (окремо по валюті) ---")
    date_from = read_date("Дата ВІД (YYYY-MM-DD або DD.MM.YYYY): ")
    date_to = read_date("Дата ДО (YYYY-MM-DD або DD.MM.YYYY): ")
    date_from, date_to = _normalize_period(date_from, date_to)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    e.currency,
                    SUM(e.amount) AS total_amount,
                    (DATE(%s) - DATE(%s) + 1) AS days_count
                FROM expenses e
                WHERE e.expense_date BETWEEN %s AND %s
                GROUP BY e.currency
                ORDER BY e.currency;
            """, (date_to, date_from, date_from, date_to))
            rows = cur.fetchall()

        if not rows:
            print("За цей період витрат немає.")
            return

        print("\nВалюта | Сума за період | Днів | Середнє/день")
        print("-" * 70)
        for curr, total, days in rows:
            days_int = int(days)
            avg = float(total) / days_int if days_int > 0 else 0
            print(f"{curr} | {total} | {days_int} | {avg:.2f}")
        print()
    finally:
        conn.close()


# ---------- 9) Експорт за період у CSV ----------
def export_expenses_by_period_to_csv():
    print("\n--- Експорт у CSV: витрати за період ---")
    date_from = read_date("Дата ВІД (YYYY-MM-DD або DD.MM.YYYY): ")
    date_to = read_date("Дата ДО (YYYY-MM-DD або DD.MM.YYYY): ")
    date_from, date_to = _normalize_period(date_from, date_to)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    e.expense_date,
                    c.name AS category,
                    e.title,
                    e.amount,
                    e.currency,
                    COALESCE(e.description, '')
                FROM expenses e
                JOIN categories c ON c.id = e.category_id
                WHERE e.expense_date BETWEEN %s AND %s
                ORDER BY e.expense_date, e.id;
            """, (date_from, date_to))
            rows = cur.fetchall()

        if not rows:
            print("За цей період витрат немає — експортувати нічого.")
            return

        os.makedirs("export", exist_ok=True)
        filename = f"export/expenses_{date_from}_to_{date_to}.csv"

        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["date", "category", "title", "amount", "currency", "description"])
            for r in rows:
                writer.writerow(r)

        print(f"✅ CSV збережено: {filename}")
    except Exception as e:
        print(" Не вдалося зробити експорт.")
        print(e)
    finally:
        conn.close()
