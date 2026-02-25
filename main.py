from logger_config import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)
logger.info("App started")

from db import init_db
from categories import categories_menu
from expenses import expenses_menu
from reports import reports_menu


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
            print("Невірний вибір")


if __name__ == "__main__":
    main()


