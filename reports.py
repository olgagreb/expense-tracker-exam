import os
import csv
from db import get_conn
from categories import list_categories, get_category_name
from utils import read_date


def report_expenses_by_period():
    print("\n--- Звіт: витрати за період ---")
    date_from = read_date("Дата ВІД (YYYY-MM-DD або DD.MM.YYYY): ")
    date_to = read_date("Дата ДО (YYYY-MM-DD або DD.MM.YYYY): ")

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT e.expense_date, c.name, e.title, e.amount, e.currency, COALESCE(e.description,'')
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
        print("-" * 95)
        for dt, cat, title, amount, curr, desc in rows:
            tail = f" | {desc}" if desc else ""
            print(f"{dt} | {cat} | {title} | {amount} {curr}{tail}")
        print()
    finally:
        conn.close()


def report_filter_by_title():
    # (вимога №1) — фільтр саме по expenses.title
    print("\n--- Фільтрація витрат за назвою витрати (title) ---")
    text = input("Введіть назву витрати або її частину: ").strip()

    if not text:
        print(" Текст не може бути порожнім")
        return

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT e.expense_date, c.name, e.title, e.amount, e.currency, COALESCE(e.description,'')
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
        print("-" * 95)
        for d, cat, title, amount, curr, desc in rows:
            tail = f" | {desc}" if desc else ""
            print(f"{d} | {cat} | {title} | {amount} {curr}{tail}")
        print()
    finally:
        conn.close()


def report_expenses_by_category_id():
    # (вимога №2) — прямий SQL WHERE e.category_id = %s
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
                SELECT e.id, e.expense_date, e.title, e.amount, e.currency, COALESCE(e.description,'')
                FROM expenses e
                WHERE e.category_id = %s
                ORDER BY e.expense_date, e.id;
            """, (category_id,))
            rows = cur.fetchall()

        if not rows:
            print("У цій категорії витрат немає.")
            return

        print("\nID | Дата | Назва | Сума | Валюта | Опис")
        print("-" * 95)
        for eid, dt, title, amount, curr, desc in rows:
            tail = f" | {desc}" if desc else ""
            print(f"{eid} | {dt} | {title} | {amount} {curr}{tail}")
        print()
    finally:
        conn.close()


def export_expenses_by_period_to_csv():
    print("\n--- Експорт у CSV: витрати за період ---")
    date_from = read_date("Дата ВІД (YYYY-MM-DD або DD.MM.YYYY): ")
    date_to = read_date("Дата ДО (YYYY-MM-DD або DD.MM.YYYY): ")

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT e.expense_date, c.name, e.title, e.amount, e.currency, COALESCE(e.description,'')
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


def reports_menu():
    while True:
        print("\n=== Звіти ===")
        print("1. Витрати за період")
        print("2. Фільтрація за назвою витрати (title)")
        print("3. Витрати по категорії (ID)")
        print("4. Експорт витрат за період у CSV")
        print("0. Назад")

        choice = input("Ваш вибір: ").strip()
        if choice == "1":
            report_expenses_by_period()
        elif choice == "2":
            report_filter_by_title()
        elif choice == "3":
            report_expenses_by_category_id()
        elif choice == "4":
            export_expenses_by_period_to_csv()
        elif choice == "0":
            return
        else:
            print(" Невірний вибір.")

