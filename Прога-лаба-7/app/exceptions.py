"""Иерархия исключений приложения."""


class AppError(Exception):
    """Базовое исключение приложения."""


class ValidationError(AppError):
    """Некорректное значение атрибута."""


class DuplicateError(AppError):
    """Нарушение уникальности (username, email, подписка)."""


class NotFoundError(AppError):
    """Объект не найден."""


class ProviderError(AppError):
    """Ошибка получения или разбора курсов."""