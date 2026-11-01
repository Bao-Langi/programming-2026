import pytest

from app.exceptions import AppError, DuplicateError, NotFoundError, ValidationError


def test_sync_currencies(tracker):
    assert [c.code for c in tracker.currencies] == ["EUR", "JPY", "USD"]
    assert tracker.sync_currencies() == 0  # повторная синхронизация ничего не добавляет


def test_register_user(tracker):
    user = tracker.register_user("anna", "a@ex.ru")
    assert tracker.get_user(user.id) is user


@pytest.mark.parametrize("username, email", [("anna", "other@ex.ru"), ("ANNA", "x@ex.ru"), ("boris", "A@EX.RU")])
def test_register_duplicate(tracker, username, email):
    tracker.register_user("anna", "a@ex.ru")
    with pytest.raises(DuplicateError):
        tracker.register_user(username, email)


def test_register_invalid(tracker):
    with pytest.raises(ValidationError):
        tracker.register_user("", "a@ex.ru")


def test_subscribe_and_rates(tracker):
    user = tracker.register_user("anna", "a@ex.ru")
    tracker.subscribe(user.id, "usd")
    tracker.subscribe(user.id, "JPY")
    assert [c.code for c in tracker.get_user_currencies(user.id)] == ["JPY", "USD"]
    assert [r.code for r in tracker.get_user_rates(user.id)] == ["JPY", "USD"]


def test_double_subscription_forbidden(tracker):
    user = tracker.register_user("anna", "a@ex.ru")
    tracker.subscribe(user.id, "USD")
    with pytest.raises(DuplicateError):
        tracker.subscribe(user.id, "USD")


def test_many_to_many(tracker):
    anna = tracker.register_user("anna", "a@ex.ru")
    boris = tracker.register_user("boris", "b@ex.ru")
    for user in (anna, boris):
        tracker.subscribe(user.id, "USD")
    tracker.subscribe(anna.id, "EUR")
    assert set(tracker.get_subscribers("USD")) == {anna, boris}
    assert len(tracker.get_user_currencies(anna.id)) == 2


def test_unsubscribe(tracker):
    user = tracker.register_user("anna", "a@ex.ru")
    tracker.subscribe(user.id, "USD")
    tracker.unsubscribe(user.id, "USD")
    assert tracker.get_user_currencies(user.id) == []
    with pytest.raises(NotFoundError):
        tracker.unsubscribe(user.id, "USD")


@pytest.mark.parametrize("user_id, code", [(999, "USD"), (1, "XXX")])
def test_not_found_is_app_error(tracker, user_id, code):
    tracker.register_user("anna", "a@ex.ru")
    with pytest.raises(AppError):
        tracker.subscribe(user_id, code)