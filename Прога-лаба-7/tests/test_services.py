import pytest

from app.exceptions import AppError, DuplicateError, InactiveUserError, NotFoundError, ValidationError

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


def test_inactive_user_cannot_subscribe(tracker):
    user = tracker.register_user("anna", "a@ex.ru")
    user.deactivate()
    with pytest.raises(InactiveUserError):
        tracker.subscribe(user.id, "USD")
    assert issubclass(InactiveUserError, AppError)

def test_save_and_load(tracker, provider, tmp_path):
    from app.services import CurrencyTracker

    anna = tracker.register_user("anna", "a@ex.ru")
    tracker.register_user("boris", "b@ex.ru")
    tracker.subscribe(anna.id, "USD")
    path = tmp_path / "data.json"
    tracker.save(path)

    other = CurrencyTracker(provider)
    other.load(path)
    assert [u.username for u in other.users] == ["anna", "boris"]
    assert other.get_user(anna.id).created_at == anna.created_at
    assert [c.code for c in other.get_user_currencies(anna.id)] == ["USD"]
    assert other.register_user("clara", "c@ex.ru").id == 3  # нумерация продолжается


def test_load_errors(tracker, tmp_path):
    with pytest.raises(NotFoundError):
        tracker.load(tmp_path / "missing.json")
    bad = tmp_path / "bad.json"
    bad.write_text("не json", encoding="utf-8")
    with pytest.raises(ValidationError):
        tracker.load(bad)