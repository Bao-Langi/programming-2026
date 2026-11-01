"""Модели предметной области."""


class User:
    """Пользователь приложения."""

    _id_counter: int = 0          # последний выданный id
    USERNAME_MIN_LENGTH = 3
    USERNAME_MAX_LENGTH = 32

    def __init__(self, username: str, email: str) -> None:
        self.id = self._generate_id()
        self.username = username
        self.email = email

    @classmethod
    def _generate_id(cls) -> int:
        cls._id_counter += 1
        return cls._id_counter

    @classmethod
    def reset_ids(cls) -> None:
        """Сбросить счётчик id. Понадобится в тестах."""
        cls._id_counter = 0

    def info(self) -> str:
        return f"{self.username} <{self.email}>"


class Currency:
    """Валюта из справочника ЦБ РФ."""

    _id_counter: int = 0
    CODE_LENGTH = 3

    def __init__(self, code: str, name: str) -> None:
        self.id = self._generate_id()
        self.code = code
        self.name = name

    @classmethod
    def _generate_id(cls) -> int:
        cls._id_counter += 1
        return cls._id_counter

    @classmethod
    def reset_ids(cls) -> None:
        """Сбросить счётчик id. Понадобится в тестах."""
        cls._id_counter = 0

    def info(self) -> str:
        return f"{self.code} — {self.name}"