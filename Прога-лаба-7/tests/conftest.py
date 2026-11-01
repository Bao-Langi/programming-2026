from datetime import date
from decimal import Decimal

import pytest

from app.models import BaseEntity, Currency, Rate, User
from app.providers import StaticRateProvider
from app.services import CurrencyTracker


@pytest.fixture(autouse=True)
def reset_ids():
    """Перед каждым тестом id снова начинаются с 1."""
    for cls in (BaseEntity, User, Currency):
        cls.reset_ids()


@pytest.fixture
def rates():
    day = date(2026, 10, 27)
    return [
        Rate("USD", "Доллар США", 1, Decimal("80.5"), day),
        Rate("EUR", "Евро", 1, Decimal("93.1"), day),
        Rate("JPY", "Японских иен", 100, Decimal("53.0"), day),
    ]


@pytest.fixture
def provider(rates):
    return StaticRateProvider(rates)


@pytest.fixture
def tracker(provider):
    service = CurrencyTracker(provider)
    service.sync_currencies()
    return service