"""Сервисный слой: регистрация пользователей и управление подписками."""
from __future__ import annotations

from app.exceptions import DuplicateError, InactiveUserError, NotFoundError
from app.models import Currency, Rate, Subscription, User
from app.providers import RateProvider


class CurrencyTracker:
    """Хранит пользователей, валюты и подписки в памяти."""

    def __init__(self, provider: RateProvider) -> None:
        self._provider = provider                       # внедрение зависимости
        self._users: dict[int, User] = {}
        self._currencies: dict[str, Currency] = {}      # ключ — код валюты
        self._subscriptions: set[Subscription] = set()

    # ---------- пользователи ----------
    def register_user(self, username: str, email: str) -> User:
        user = User(username, email)      # сначала проверка данных в модели
        for existing in self._users.values():
            if existing.username.lower() == user.username.lower():
                raise DuplicateError(f"Имя {user.username!r} уже занято")
            if existing.email == user.email:
                raise DuplicateError(f"Email {user.email!r} уже зарегистрирован")
        self._users[user.id] = user
        return user

    def get_user(self, user_id: int) -> User:
        try:
            return self._users[user_id]
        except KeyError:
            raise NotFoundError(f"Пользователь с id={user_id} не найден") from None

    @property
    def users(self) -> list[User]:
        return list(self._users.values())

    # ---------- валюты ----------
    def sync_currencies(self) -> int:
        """Обновить справочник по данным поставщика. Вернуть число новых валют."""
        added = 0
        for code, rate in self._provider.get_rates().items():
            if code in self._currencies:
                self._currencies[code].name = rate.name
            else:
                self._currencies[code] = Currency(code, rate.name)
                added += 1
        return added

    def get_currency(self, code: str) -> Currency:
        code = code.strip().upper()
        try:
            return self._currencies[code]
        except KeyError:
            raise NotFoundError(f"Валюта {code} не найдена") from None

    @property
    def currencies(self) -> list[Currency]:
        return sorted(self._currencies.values(), key=lambda c: c.code)

    # ---------- подписки ----------
    def subscribe(self, user_id: int, code: str) -> Subscription:
        user = self.get_user(user_id)
        if not user.is_active:
            raise InactiveUserError(f"Пользователь {user.username!r} неактивен")
        subscription = Subscription(user, self.get_currency(code))
        if subscription in self._subscriptions:
            raise DuplicateError("Подписка уже существует")
        self._subscriptions.add(subscription)
        return subscription

    def unsubscribe(self, user_id: int, code: str) -> None:
        subscription = Subscription(self.get_user(user_id), self.get_currency(code))
        if subscription not in self._subscriptions:
            raise NotFoundError("Подписка не найдена")
        self._subscriptions.remove(subscription)

    def get_user_currencies(self, user_id: int) -> list[Currency]:
        user = self.get_user(user_id)
        found = [s.currency for s in self._subscriptions if s.user == user]
        return sorted(found, key=lambda c: c.code)

    def get_subscribers(self, code: str) -> list[User]:
        currency = self.get_currency(code)
        return [s.user for s in self._subscriptions if s.currency == currency]

    def get_user_rates(self, user_id: int) -> list[Rate]:
        rates = self._provider.get_rates()
        return [rates[c.code] for c in self.get_user_currencies(user_id) if c.code in rates]