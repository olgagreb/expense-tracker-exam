from db import get_conn


def add_category():
    name = input("Введіть назву категорії: ").strip()
    if not name:
        print(" Назва не може бути порожньою.")
        return

    conn = get_conn()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO categories (name) VALUES (%s);", (name,))
        print(" Категорію додано")
    except Exception as e:
        print(" Не вдалося додати категорію (можливо, така вже існує)")
        print(e)
    finally:
        conn.close()


def list_categories() -> list[tuple[int, str]]:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM categories ORDER BY id;")
            rows = cur.fetchall()

        if not rows:
            print("Поки немає жодної категорії.")
            return []

        print("\nКатегорії:")
        for cid, name in rows:
            print(f"{cid}. {name}")
        print()
        return rows
    finally:
        conn.close()


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


def update_category():
    print("\n--- Редагування категорії ---")
    list_categories()

    raw = input("Введіть ID категорії для редагування: ").strip()
    if not raw.isdigit():
        print(" ID має бути числом")
        return
    cid = int(raw)

    new_name = input("Нова назва категорії: ").strip()
    if not new_name:
        print(" Назва не може бути порожньою.")
        return

    conn = get_conn()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE categories SET name = %s WHERE id = %s;", (new_name, cid))
            if cur.rowcount == 0:
                print(" Категорію з таким ID не знайдено")
            else:
                print(" Категорію оновлено")
    except Exception as e:
        print(" Не вдалося оновити категорію (можливо, така назва вже існує)")
        print(e)
    finally:
        conn.close()


def delete_category():
    list_categories()
    raw = input("Введіть ID категорії для видалення: ").strip()
    if not raw.isdigit():
        print(" ID має бути числом")
        return
    cid = int(raw)

    conn = get_conn()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM categories WHERE id = %s;", (cid,))
            if cur.rowcount == 0:
                print(" Категорію з таким ID не знайдено")
            else:
                print(" Категорію видалено")
    except Exception as e:
        print(" Не вдалося видалити категорію (можливо, вона вже використовується у витратах)")
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
            print(" Невірний вибір")
