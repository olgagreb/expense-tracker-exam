from db import get_conn
from categories import list_categories, get_category_name, find_category_id_by_text
from utils import (
    read_amount, read_date, read_currency,
    read_optional_amount, read_optional_date, read_optional_currency
)


def read_category_id_or_keyword() -> tuple[int, str] | None:
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
    expense_date = read_date("Дата (YYYY-MM-DD або DD.MM.YYYY): ")
    currency = read_currency()

    list_categories()
    result = read_category_id_or_keyword()
    if not result:
        print(" Категорію не знайдено.")
        return

    cat_id, category_name = result

    title_input = input("Назва витрати (Enter = назва категорії): ").strip()
    title = category_name if title_input == "" else title_input

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
        print(" Витрату додано")
    except Exception as e:
        print(" Не вдалося додати витрату")
        print(e)
    finally:
        conn.close()


def list_expenses():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT e.id, e.expense_date, e.title, e.amount, e.currency, c.name, COALESCE(e.description, '')
                FROM expenses e
                JOIN categories c ON c.id = e.category_id
                ORDER BY e.expense_date DESC, e.id DESC;
            """)
            rows = cur.fetchall()

        if not rows:
            print("Поки немає жодної витрати.")
            return

        print("\nВитрати:")
        for eid, dt, title, amount, currency, cat_name, desc in rows:
            tail = f" | {desc}" if desc else ""
            print(f"{eid}. {dt} | {cat_name} | {title} | {amount} {currency}{tail}")
        print()
    finally:
        conn.close()


def view_expense_details():
    print("\n--- Перегляд витрати (деталі) ---")
    raw = input("Введіть ID витрати: ").strip()

    if not raw.isdigit():
        print(" ID має бути числом.")
        return

    expense_id = int(raw)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT e.id, e.title, e.expense_date, c.name, e.amount, e.currency, e.description
                FROM expenses e
                JOIN categories c ON c.id = e.category_id
                WHERE e.id = %s;
            """, (expense_id,))
            row = cur.fetchone()

        if not row:
            print(" Витрату з таким ID не знайдено.")
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
        print(" ID має бути числом.")
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
                print(" Витрату з таким ID не знайдено.")
                return

            eid, old_title, old_date, old_cat_id, old_amount, old_currency, old_desc = row

            print("\nПоточні значення:")
            print(f"ID: {eid}")
            print(f"Назва: {old_title}")
            print(f"Дата: {old_date}")
            print(f"Категорія ID: {old_cat_id} ({get_category_name(old_cat_id)})")
            print(f"Сума: {old_amount} {old_currency}")
            print(f"Опис: {old_desc if old_desc else '(немає)'}")

            print("\nВведіть нові значення або Enter, щоб залишити як було.")

            new_title = input("Нова назва: ").strip() or None
            new_date = read_optional_date("Нова дата (Enter = не змінювати): ")

            raw_cat = input("Нова категорія (ID/слово, Enter = не змінювати): ").strip()
            new_cat_id = None
            if raw_cat != "":
                if raw_cat.isdigit():
                    cid = int(raw_cat)
                    if get_category_name(cid) is None:
                        print(" Категорію з таким ID не знайдено.")
                        return
                    new_cat_id = cid
                else:
                    cid = find_category_id_by_text(raw_cat)
                    if cid is None or get_category_name(cid) is None:
                        print(" Категорію не знайдено.")
                        return
                    new_cat_id = cid

            new_amount = read_optional_amount("Нова сума (Enter = не змінювати): ")
            new_currency = read_optional_currency()

            new_desc = input("Новий опис (Enter = не змінювати, '-' = очистити): ").strip()
            if new_desc == "":
                new_desc = None
            elif new_desc == "-":
                new_desc = ""

            final_title = old_title if new_title is None else new_title
            final_date = old_date if new_date is None else new_date
            final_cat_id = old_cat_id if new_cat_id is None else new_cat_id
            final_amount = old_amount if new_amount is None else new_amount
            final_currency = old_currency if new_currency is None else new_currency

            if new_desc is None:
                final_desc = old_desc
            else:
                final_desc = None if new_desc == "" else new_desc

            cur.execute("""
                UPDATE expenses
                SET title=%s, expense_date=%s, category_id=%s, amount=%s, currency=%s, description=%s
                WHERE id=%s;
            """, (final_title, final_date, final_cat_id, final_amount, final_currency, final_desc, expense_id))

            print(" Витрату оновлено.")
    except Exception as e:
        print(" Не вдалося оновити витрату.")
        print(e)
    finally:
        conn.close()


def delete_expense():
    print("\n--- Видалення витрати ---")
    raw = input("Введіть ID витрати для видалення: ").strip()

    if not raw.isdigit():
        print(" ID має бути числом.")
        return

    expense_id = int(raw)

    conn = get_conn()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT e.id, e.expense_date, e.title, e.amount, e.currency, c.name, COALESCE(e.description,'')
                FROM expenses e
                JOIN categories c ON c.id = e.category_id
                WHERE e.id = %s;
            """, (expense_id,))
            row = cur.fetchone()

            if not row:
                print(" Витрату з таким ID не знайдено.")
                return

            eid, dt, title, amount, currency, cat_name, desc = row
            tail = f" | {desc}" if desc else ""
            print(f"Знайдено: ID={eid} | {dt} | {cat_name} | {title} | {amount} {currency}{tail}")

            while True:
                confirm = input("Підтвердіть видалення (так/ні): ").strip().lower()
                if confirm == "так":
                    cur.execute("DELETE FROM expenses WHERE id = %s;", (expense_id,))
                    print(" Витрату видалено.")
                    break
                if confirm == "ні":
                    print(" Видалення скасовано.")
                    break
                print(" Введіть саме 'так' або 'ні'.")
    except Exception as e:
        print(" Не вдалося видалити витрату.")
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
            print(" Невірний вибір")
