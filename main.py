import psycopg2
from datetime import datetime

import os
import csv


DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "expense_exam"
DB_USER = "postgres"
DB_PASSWORD = "10072012tima"


# ---------- DB ----------
def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def init_db():
    conn = get_conn()
    conn.autocommit = True
    with conn.cursor() as cur:

        cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
            expense_date DATE NOT NULL,
            category_id INT NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
            description TEXT,
            currency VARCHAR(10) DEFAULT 'UAH'
        );
        """)


        cur.execute("ALTER TABLE expenses ADD COLUMN IF NOT EXISTS currency VARCHAR(10);")
        cur.execute("ALTER TABLE expenses ALTER COLUMN currency SET DEFAULT 'UAH';")
        cur.execute("UPDATE expenses SET currency = 'UAH' WHERE currency IS NULL;")

    conn.close()


# ---------- helpers ----------
def read_int(prompt: str) -> int:
    while True:
        s = input(prompt).strip()
        if s.isdigit():
            return int(s)
        print("❌ Введіть ціле число.")


def read_amount(prompt: str) -> float:
    while True:
        s = input(prompt).strip().lower()

        # дозволяємо "грн", пробіли, коми
        s = s.replace("грн", "").replace(" ", "").replace(",", ".")

        try:
            value = float(s)
            if value <= 0:
                print("❌ Сума має бути більшою за 0.")
                continue
            return value
        except ValueError:
            print("❌ Введіть число (наприклад 125.50 або 3400 грн).")


def read_optional_amount(prompt: str) -> float | None:
    s = input(prompt).strip().lower()
    if s == "":
        return None
    s = s.replace("грн", "").replace(" ", "").replace(",", ".")
    try:
        value = float(s)
        if value <= 0:
            print("❌ Сума має бути більшою за 0.")
            return read_optional_amount(prompt)
        return value
    except ValueError:
        print("❌ Введіть число (наприклад 125.50 або 3400 грн) або Enter щоб не змінювати.")
        return read_optional_amount(prompt)


def read_date_ua(prompt: str) -> str:
    """
    Ввід: ДД.ММ.РРРР (01.02.2026)
    Вихід: YYYY-MM-DD (для PostgreSQL)
    """
    while True:
        s = input(prompt).strip()
        try:
            dt = datetime.strptime(s, "%d.%m.%Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            print("❌ Дата має бути у форматі ДД.ММ.РРРР (наприклад 01.02.2026).")


def read_optional_date(prompt: str) -> str | None:
    s = input(prompt).strip()
    if s == "":
        return None
    # підтримуємо 2 формати: DD.MM.YYYY і YYYY-MM-DD
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    print("❌ Дата має бути у форматі ДД.ММ.РРРР або РРРР-ММ-ДД. Або Enter щоб не змінювати.")
    return read_optional_date(prompt)


ALLOWED_CURRENCIES = {"UAH", "USD", "EUR"}


def read_currency(prompt: str = "Валюта (Enter = UAH, UAH/USD/EUR): ") -> str:
    while True:
        s = input(prompt).strip().upper()
        if s == "":
            return "UAH"
        if s in ALLOWED_CURRENCIES:
            return s
        print("❌ Невірна валюта. Дозволено: UAH, USD, EUR. Або натисніть Enter для UAH.")


def read_optional_currency(prompt: str = "Валюта (Enter = не змінювати): ") -> str | None:
    s = input(prompt).strip().upper()
    if s == "":
        return None
    if s in ALLOWED_CURRENCIES:
        return s
    print("❌ Невірна валюта. Дозволено: UAH, USD, EUR. Або Enter щоб не змінювати.")
    return read_optional_currency(prompt)


# ---------- categories ----------
def add_category():
    name = input("Введіть назву категорії: ").strip()
    if not name:
        print("❌ Назва не може бути порожньою.")
        return

    conn = get_conn()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO categories (name) VALUES (%s);", (name,))
        print("✅ Категорію додано")
    except Exception as e:
        print("❌ Не вдалося додати категорію (можливо, така вже існує)")
        print(e)
    finally:
        conn.close()


def list_categories():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM categories ORDER BY id;")
            rows = cur.fetchall()

        if not rows:
            print("Поки немає жодної категорії.")
            return

        print("\nКатегорії:")
        for cid, name in rows:
            print(f"{cid}. {name}")
        print()
    finally:
        conn.close()



def update_category():
    print("\n--- Редагування категорії ---")
    list_categories()

    raw = input("Введіть ID категорії для редагування: ").strip()
    if not raw.isdigit():
        print("❌ ID має бути числом")
        return
    cid = int(raw)

    new_name = input("Нова назва категорії: ").strip()
    if not new_name:
        print("❌ Назва не може бути порожньою.")
        return

    conn = get_conn()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE categories SET name = %s WHERE id = %s;", (new_name, cid))
            if cur.rowcount == 0:
                print("❌ Категорію з таким ID не знайдено")
            else:
                print("✅ Категорію оновлено")
    except Exception as e:
        print("❌ Не вдалося оновити категорію (можливо, така назва вже існує)")
        print(e)
    finally:
        conn.close()


def delete_category():
    list_categories()
    raw = input("Введіть ID категорії для видалення: ").strip()
    if not raw.isdigit():
        print("❌ ID має бути числом")
        return
    cid = int(raw)

    conn = get_conn()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM categories WHERE id = %s;", (cid,))
            if cur.rowcount == 0:
                print("❌ Категорію з таким ID не знайдено")
            else:
                print("✅ Категорію видалено")
    except Exception as e:
        print("❌ Не вдалося видалити категорію (можливо, вона вже використовується у витратах)")
        print(e)
    finally:
        conn.close()


def categories_menu():
    while True:
        print("\n=== Категорії ===")
        print("1. Додати категорію")
        print("2. Показати категорії")
        print("3. Редагувати категорію")
        print("4. Видалити категорію")
        print("0. Назад")

        choice = input("Ваш вибір: ").strip()
        if choice == "1":
            add_category()
        elif choice == "2":
            list_categories()
        elif choice == "3":
            update_category()
        elif choice == "4":
            delete_category()
        elif choice == "0":
            return
        else:
            print("❌ Невірний вибір")


# ---------- expenses ----------
def get_category_name(cat_id: int) -> str | None:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM categories WHERE id = %s;", (cat_id,))
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        conn.close()


def find_category_id_by_text(text: str) -> int | None:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id
                FROM categories
                WHERE LOWER(name) LIKE LOWER(%s)
                ORDER BY id
                LIMIT 1;
            """, (f"%{text}%",))
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        conn.close()


def read_category_id_or_keyword() -> tuple[int, str] | None:
    """
    Повертає (cat_id, category_name) або None, якщо не знайдено.
    Дозволяє вводити: 5 або "транспорт" або "тран"
    """
    raw = input("ID або ключове слово категорії: ").strip()
    if not raw:
        return None

    if raw.isdigit():
        cat_id = int(raw)
    else:
        cat_id = find_category_id_by_text(raw)
        if cat_id is None:
            return None

    name = get_category_name(cat_id)
    if not name:
        return None

    return cat_id, name


def add_expense():
    print("\n--- Додавання витрати ---")

    amount = read_amount("Сума: ")
    expense_date = read_date_ua("Дата (ДД.ММ.РРРР): ")
    currency = read_currency()

    list_categories()
    result = read_category_id_or_keyword()
    if not result:
        print("❌ Категорію не знайдено.")
        return

    cat_id, category_name = result

    title_input = input("Назва витрати (Enter = назва категорії): ").strip()
    if title_input == "":
        title = category_name
    else:
        title = title_input

    description = input("Опис (необов'язково): ").strip()
    if description == "":
        description = None

    conn = get_conn()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO expenses (title, amount, expense_date, category_id, description, currency)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (title, amount, expense_date, cat_id, description, currency))

        print("✅ Витрату додано")
    except Exception as e:
        print("❌ Не вдалося додати витрату")
        print(e)
    finally:
        conn.close()


def list_expenses():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT e.id, e.expense_date, e.amount, e.currency, c.name, COALESCE(e.description, '')
                FROM expenses e
                JOIN categories c ON c.id = e.category_id
                ORDER BY e.expense_date DESC, e.id DESC;
            """)
            rows = cur.fetchall()

        if not rows:
            print("Поки немає жодної витрати.")
            return

        print("\nВитрати:")
        for eid, dt, amount, currency, cat_name, desc in rows:
            tail = f" | {desc}" if desc else ""
            print(f"{eid}. {dt} | {cat_name} | {amount} {currency}{tail}")
        print()
    finally:
        conn.close()


def view_expense_details():
    print("\n--- Перегляд витрати (деталі) ---")
    raw = input("Введіть ID витрати: ").strip()

    if not raw.isdigit():
        print("❌ ID має бути числом.")
        return

    expense_id = int(raw)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT e.id,
                       e.title,
                       e.expense_date,
                       c.name AS category,
                       e.amount,
                       e.currency,
                       e.description
                FROM expenses e
                JOIN categories c ON c.id = e.category_id
                WHERE e.id = %s;
            """, (expense_id,))
            row = cur.fetchone()

        if not row:
            print("❌ Витрату з таким ID не знайдено.")
            return

        eid, title, dt, category, amount, currency, description = row

        print("\n=== Деталі витрати ===")
        print(f"ID:        {eid}")
        print(f"Дата:      {dt}")
        print(f"Категорія:  {category}")
        print(f"Назва:     {title}")
        print(f"Сума:      {amount} {currency}")
        print(f"Опис:      {description if description else '(немає)'}")
        print()
    finally:
        conn.close()


def update_expense():
    print("\n--- Редагування витрати ---")
    raw = input("Введіть ID витрати для редагування: ").strip()
    if not raw.isdigit():
        print("❌ ID має бути числом.")
        return
    expense_id = int(raw)

    conn = get_conn()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, title, expense_date, category_id, amount, currency, description
                FROM expenses
                WHERE id = %s;
            """, (expense_id,))
            row = cur.fetchone()

            if not row:
                print("❌ Витрату з таким ID не знайдено.")
                return

            eid, old_title, old_date, old_cat_id, old_amount, old_currency, old_desc = row

            print("\nПоточні значення:")
            print(f"ID: {eid}")
            print(f"Назва: {old_title}")
            print(f"Дата: {old_date}")
            print(f"Категорія ID: {old_cat_id} ({get_category_name(old_cat_id)})")
            print(f"Сума: {old_amount} {old_currency}")
            print(f"Опис: {old_desc if old_desc else '(немає)'}")

            print("\nВведіть нові значення або натисніть Enter, щоб залишити як було.")

            new_title = input("Нова назва: ").strip()
            if new_title == "":
                new_title = None

            new_date = read_optional_date("Нова дата (ДД.ММ.РРРР або РРРР-ММ-ДД): ")

            raw_cat = input("Нова категорія (ID/слово, Enter = не змінювати): ").strip()
            new_cat_id = None
            if raw_cat != "":
                if raw_cat.isdigit():
                    cid = int(raw_cat)
                    if get_category_name(cid) is None:
                        print("❌ Категорію з таким ID не знайдено.")
                        return
                    new_cat_id = cid
                else:
                    cid = find_category_id_by_text(raw_cat)
                    if cid is None or get_category_name(cid) is None:
                        print("❌ Категорію не знайдено.")
                        return
                    new_cat_id = cid

            new_amount = read_optional_amount("Нова сума: ")
            new_currency = read_optional_currency()

            new_desc = input("Новий опис (Enter = не змінювати, '-' = очистити): ").strip()
            if new_desc == "":
                new_desc = None   # не змінювати
            elif new_desc == "-":
                new_desc = ""     # очистити

            final_title = old_title if new_title is None else new_title
            final_date = old_date if new_date is None else new_date
            final_cat_id = old_cat_id if new_cat_id is None else new_cat_id
            final_amount = old_amount if new_amount is None else new_amount
            final_currency = old_currency if new_currency is None else new_currency

            if new_desc is None:
                final_desc = old_desc
            else:
                final_desc = new_desc if new_desc != "" else None

            cur.execute("""
                UPDATE expenses
                SET title = %s,
                    expense_date = %s,
                    category_id = %s,
                    amount = %s,
                    currency = %s,
                    description = %s
                WHERE id = %s;
            """, (final_title, final_date, final_cat_id, final_amount, final_currency, final_desc, expense_id))

            print("✅ Витрату оновлено.")
    except Exception as e:
        print("❌ Не вдалося оновити витрату.")
        print(e)
    finally:
        conn.close()


def delete_expense():
    print("\n--- Видалення витрати ---")
    raw = input("Введіть ID витрати для видалення: ").strip()

    if not raw.isdigit():
        print("❌ ID має бути числом.")
        return

    expense_id = int(raw)

    conn = get_conn()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT e.id, e.expense_date, e.amount, e.currency,
                       c.name, COALESCE(e.description,'')
                FROM expenses e
                JOIN categories c ON c.id = e.category_id
                WHERE e.id = %s;
            """, (expense_id,))
            row = cur.fetchone()

            if not row:
                print("❌ Витрату з таким ID не знайдено.")
                return

            eid, dt, amount, currency, cat_name, desc = row
            tail = f" | {desc}" if desc else ""

            print(f"Знайдено: ID={eid} | {dt} | {cat_name} | {amount} {currency}{tail}")

            while True:
                confirm = input("Підтвердіть видалення (так/ні): ").strip().lower()

                if confirm == "так":
                    cur.execute("DELETE FROM expenses WHERE id = %s;", (expense_id,))
                    print("✅ Витрату видалено.")
                    break
                elif confirm == "ні":
                    print("✅ Видалення скасовано.")
                    break
                else:
                    print("❌ Введіть саме 'так' або 'ні'.")
    except Exception as e:
        print("❌ Не вдалося видалити витрату.")
        print(e)
    finally:
        conn.close()


def expenses_menu():
    while True:
        print("\n=== Витрати ===")
        print("1. Додати витрату")
        print("2. Показати витрати")
        print("3. Переглянути витрату (деталі)")
        print("4. Редагувати витрату")
        print("5. Видалити витрату")
        print("0. Назад")

        choice = input("Ваш вибір: ").strip()
        if choice == "1":
            add_expense()
        elif choice == "2":
            list_expenses()
        elif choice == "3":
            view_expense_details()
        elif choice == "4":
            update_expense()
        elif choice == "5":
            delete_expense()
        elif choice == "0":
            return
        else:
            print("❌ Невірний вибір")


def reports_menu():
    while True:
        print("\n=== Звіти ===")
        print("1. Витрати за період")
        print("2. Фільтрація за назвою категорії / описом")
        print("3. Максимальна витрата у кожній категорії")
        print("4. Максимальна витрата у періоді")
        print("5. Мінімальна витрата у кожній категорії")
        print("6. Мінімальна витрата у періоді")
        print("7. Підсумки по категоріях (підменю)")
        print("8. Експорт витрат за період у CSV")
        print("0. Назад")

        choice = input("Ваш вибір: ").strip()
        if choice == "1":
            report_expenses_by_period()
        elif choice == "2":
            report_filter_by_name()
        elif choice == "3":
            report_max_expense_per_category()
        elif choice == "4":
            report_max_expense_in_period()
        elif choice == "5":
            report_min_expense_per_category()
        elif choice == "6":
            report_min_expense_in_period()
        elif choice == "7":
            summary_menu()
        elif choice == "8":
            export_expenses_by_period_to_csv()
        elif choice == "0":
            return
        else:
            print("❌ Невірний вибір.")
            print("👉 Введіть:")
            print("   1 — витрати за період")
            print("   2 — фільтрація за назвою категорії / описом")
            print("   3 — максимальна витрата у кожній категорії")
            print("   4 — максимальна витрата у періоді")
            print("   5 — мінімальна витрата у кожній категорії")
            print("   6 — мінімальна витрата у періоді")
            print("   7 — підсумки по категоріях (підменю)")
            print("   8 — експорт витрат за період у CSV")
            print("   0 — назад")


def summary_menu():
    while True:
        print("\n=== Підсумки по категоріях ===")
        print("1. Сума по кожній категорії")
        print("2. ТОП категорія (найбільша сума)")
        print("3. Середні витрати на день за період (бонус)")
        print("0. Назад")

        choice = input("Ваш вибір: ").strip()
        if choice == "1":
            report_sum_by_category()
        elif choice == "2":
            report_top_category()
        elif choice == "3":
            report_avg_per_day_in_period()
        elif choice == "0":
            return
        else:
            print("❌ Невірний вибір.")
            print("👉 Введіть: 1, 2, 3 або 0")


def report_expenses_by_period():
    print("\n--- Звіт: витрати за період ---")

    date_from = read_date_ua("Дата ВІД (ДД.ММ.РРРР): ")
    date_to = read_date_ua("Дата ДО (ДД.ММ.РРРР): ")

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    e.expense_date,
                    c.name,
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

        print("\nДата | Категорія | Сума | Валюта | Опис")
        print("-" * 70)
        for dt, cat, amount, currency, desc in rows:
            tail = f" | {desc}" if desc else ""
            print(f"{dt} | {cat} | {amount} | {currency}{tail}")
        print()
    finally:
        conn.close()


def report_sum_by_category():
    print("\n--- Підсумки: сума витрат по категоріях (окремо по валюті) ---")

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    c.name,
                    e.currency,
                    SUM(e.amount) AS total_amount
                FROM expenses e
                JOIN categories c ON c.id = e.category_id
                GROUP BY c.name, e.currency
                ORDER BY c.name, e.currency;
            """)
            rows = cur.fetchall()

        if not rows:
            print("Витрат поки що немає.")
            return

        print("\nКатегорія | Валюта | Загальна сума")
        print("-" * 50)
        for name, curr, total in rows:
            print(f"{name} | {curr} | {total}")
        print()
    finally:
        conn.close()


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

        print("\nКатегорія | Валюта | ID | Дата | Сума | Опис")
        print("-" * 90)
        for cat, curr, eid, dt, amount, desc in rows:
            tail = f" | {desc}" if desc else ""
            print(f"{cat} | {curr} | {eid} | {dt} | {amount} {curr}{tail}")
        print()
    finally:
        conn.close()


def report_max_expense_in_period():
    print("\n--- Звіт: максимальна витрата у періоді (окремо по валюті) ---")

    date_from = read_date_ua("Дата ВІД (ДД.ММ.РРРР): ")
    date_to = read_date_ua("Дата ДО (ДД.ММ.РРРР): ")

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT ON (e.currency)
                    e.currency,
                    e.id,
                    e.expense_date,
                    c.name AS category,
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
        for curr, eid, dt, cat, amount, desc in rows:
            tail = f" | {desc}" if desc else ""
            print(f"{curr}: ID={eid} | {dt} | {cat} | {amount} {curr}{tail}")
        print()
    finally:
        conn.close()


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

        print("\nКатегорія | Валюта | ID | Дата | Сума | Опис")
        print("-" * 90)
        for cat, curr, eid, dt, amount, desc in rows:
            tail = f" | {desc}" if desc else ""
            print(f"{cat} | {curr} | {eid} | {dt} | {amount} {curr}{tail}")
        print()
    finally:
        conn.close()


def report_min_expense_in_period():
    print("\n--- Звіт: мінімальна витрата у періоді (окремо по валюті) ---")

    date_from = read_date_ua("Дата ВІД (ДД.ММ.РРРР): ")
    date_to = read_date_ua("Дата ДО (ДД.ММ.РРРР): ")

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT ON (e.currency)
                    e.currency,
                    e.id,
                    e.expense_date,
                    c.name AS category,
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
        for curr, eid, dt, cat, amount, desc in rows:
            tail = f" | {desc}" if desc else ""
            print(f"{curr}: ID={eid} | {dt} | {cat} | {amount} {curr}{tail}")
        print()
    finally:
        conn.close()


def report_top_category():
    print("\n--- Підсумки: ТОП категорія за сумою (окремо по валюті) ---")

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                WITH sums AS (
                    SELECT c.name AS category, e.currency, SUM(e.amount) AS total_amount
                    FROM expenses e
                    JOIN categories c ON c.id = e.category_id
                    GROUP BY c.name, e.currency
                )
                SELECT DISTINCT ON (currency)
                    currency, category, total_amount
                FROM sums
                ORDER BY currency, total_amount DESC;
            """)
            rows = cur.fetchall()

        if not rows:
            print("Витрат поки що немає.")
            return

        print("\nВалюта | ТОП категорія | Сума")
        print("-" * 45)
        for curr, cat, total in rows:
            print(f"{curr} | {cat} | {total}")
        print()
    finally:
        conn.close()


def report_avg_per_day_in_period():
    print("\n--- Підсумки (бонус): середні витрати на день за період ---")

    date_from = read_date_ua("Дата ВІД (ДД.ММ.РРРР): ")
    date_to = read_date_ua("Дата ДО (ДД.ММ.РРРР): ")

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
        print("-" * 60)
        for curr, total, days in rows:
            avg = float(total) / int(days) if int(days) > 0 else 0
            print(f"{curr} | {total} | {days} | {avg:.2f}")
        print()
    finally:
        conn.close()


def report_filter_by_name():
    print("\n--- Фільтрація витрат за назвою категорії / описом ---")
    text = input("Введіть текст для пошуку: ").strip()

    if not text:
        print("❌ Текст не може бути порожнім")
        return

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    e.expense_date,
                    c.name,
                    e.amount,
                    e.currency,
                    COALESCE(e.description, '')
                FROM expenses e
                JOIN categories c ON c.id = e.category_id
                WHERE
                    LOWER(c.name) LIKE LOWER(%s)
                    OR LOWER(COALESCE(e.description, '')) LIKE LOWER(%s)
                ORDER BY e.expense_date, e.id;
            """, (f"%{text}%", f"%{text}%"))

            rows = cur.fetchall()

        if not rows:
            print("Нічого не знайдено.")
            return

        print("\nДата | Категорія | Сума | Валюта | Опис")
        print("-" * 70)
        for d, cat, amount, curr, desc in rows:
            tail = f" | {desc}" if desc else ""
            print(f"{d} | {cat} | {amount} | {curr}{tail}")
        print()
    finally:
        conn.close()

def export_expenses_by_period_to_csv():
    print("\n--- Експорт у CSV: витрати за період ---")

    date_from = read_date_ua("Дата ВІД (ДД.ММ.РРРР): ")
    date_to = read_date_ua("Дата ДО (ДД.ММ.РРРР): ")

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    e.expense_date,
                    c.name,
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
        print("❌ Не вдалося зробити експорт.")
        print(e)
    finally:
        conn.close()



# ---------- main ----------
def main():
    init_db()
    while True:
        print("\n=== Облік витрат ===")
        print("1. Категорії")
        print("2. Витрати")
        print("3. Звіти")
        print("0. Вихід")

        choice = input("Ваш вибір: ").strip()
        if choice == "1":
            categories_menu()
        elif choice == "2":
            expenses_menu()
        elif choice == "3":
            reports_menu()
        elif choice == "0":
            print("До побачення!")
            break
        else:
            print("❌ Невірний вибір")


if __name__ == "__main__":
    main()

