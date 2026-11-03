"""Консольный интерфейс трекера курсов валют."""
import sys

from app.exceptions import AppError, ProviderError
from app.providers import CbrXmlProvider, RateProvider, StaticRateProvider
from app.services import CurrencyTracker

MENU = """
1. Зарегистрироваться
2. Список валют
3. Подписаться на валюту
4. Отписаться от валюты
5. Мои курсы
6. Подписчики валюты
0. Выход
"""

def choose_provider() -> RateProvider:
    if "--offline" in sys.argv:
        return StaticRateProvider.demo()
    return CbrXmlProvider()


def ask_user_id() -> int:
    return int(input("Ваш id: "))


def load_tracker() -> CurrencyTracker | None:
    """Создать трекер и загрузить валюты. При сбое предложить автономный режим."""
    tracker = CurrencyTracker(choose_provider())
    try:
        added = tracker.sync_currencies()
    except ProviderError as exc:
        # except: сеть недоступна, предлагаем демо-данные
        print(f"Ошибка: {exc}")
        if input("Перейти в автономный режим? (y/n): ").strip().lower() != "y":
            print("Запустите программу с ключом --offline")
            return None
        tracker = CurrencyTracker(StaticRateProvider.demo())
        print(f"Загружено валют (демо): {tracker.sync_currencies()}")
    else:
        # else: выполняется только если ошибки не было
        print(f"Загружено валют: {added}")
    finally:
        # finally: выполняется в любом случае
        print("Синхронизация завершена")
    return tracker


def main() -> None:
    tracker = load_tracker()
    if tracker is None:
        return

    while True:
        print(MENU)
        choice = input("Выберите пункт: ").strip()
        try:
            if choice == "1":
                user = tracker.register_user(input("Имя: "), input("Email: "))
                print(f"Зарегистрирован: {user} (id={user.id})")
            elif choice == "2":
                for currency in tracker.currencies:
                    print(currency)
            elif choice == "3":
                tracker.subscribe(ask_user_id(), input("Код валюты: "))
                print("Подписка оформлена")
            elif choice == "4":
                tracker.unsubscribe(ask_user_id(), input("Код валюты: "))
                print("Подписка отменена")
            elif choice == "5":
                rates = tracker.get_user_rates(ask_user_id())
                for rate in sorted(rates, reverse=True):
                    print(rate)
            elif choice == "6":
                for user in tracker.get_subscribers(input("Код валюты: ")):
                    print(user)
            elif choice == "0":
                break
            else:
                print("Нет такого пункта")
        except ProviderError as exc:
            print(f"Ошибка сети: {exc}")
        except AppError as exc:
            print(f"Ошибка: {exc}")
        except ValueError:
            print("Ошибка: id должен быть целым числом")


if __name__ == "__main__":
    main()