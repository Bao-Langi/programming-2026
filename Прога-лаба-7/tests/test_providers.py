from decimal import Decimal

import pytest
import requests

from app.exceptions import NotFoundError, ProviderError
from app.providers import CbrJsonProvider, CbrXmlProvider, RateProvider, StaticRateProvider

SAMPLE_XML = """<?xml version="1.0" encoding="windows-1251"?>
<ValCurs Date="27.10.2026" name="Foreign Currency Market">
<Valute ID="R01235"><NumCode>840</NumCode><CharCode>USD</CharCode><Nominal>1</Nominal>
<Name>Доллар США</Name><Value>80,5000</Value></Valute>
<Valute ID="R01820"><NumCode>392</NumCode><CharCode>JPY</CharCode><Nominal>100</Nominal>
<Name>Японских иен</Name><Value>53,0000</Value></Valute>
</ValCurs>""".encode("windows-1251")


def test_abstract_provider_cannot_be_created():
    with pytest.raises(TypeError):
        RateProvider()


def test_cbr_parse():
    rates = CbrXmlProvider.parse(SAMPLE_XML)
    assert set(rates) == {"USD", "JPY"}
    assert rates["USD"].name == "Доллар США"
    assert rates["JPY"].per_unit == Decimal("0.53")


def test_cbr_parse_broken_xml():
    with pytest.raises(ProviderError):
        CbrXmlProvider.parse(b"<not xml")


def test_cbr_network_error(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.ConnectionError("нет сети")

    monkeypatch.setattr(requests, "get", fake_get)
    with pytest.raises(ProviderError):
        CbrXmlProvider().get_rates()


def test_cbr_uses_response(monkeypatch):
    class FakeResponse:
        content = SAMPLE_XML

        def raise_for_status(self):
            pass

    monkeypatch.setattr(requests, "get", lambda *a, **kw: FakeResponse())
    assert "USD" in CbrXmlProvider().get_rates()


@pytest.mark.parametrize("make_provider", [
    lambda rates: StaticRateProvider(rates),
    lambda rates: StaticRateProvider.demo(),
])
def test_any_provider_has_same_interface(make_provider, rates):
    provider = make_provider(rates)
    assert isinstance(provider, RateProvider)
    assert provider.get_rate("usd").code == "USD"
    with pytest.raises(NotFoundError):
        provider.get_rate("XXX")


BROKEN_XML = """<?xml version="1.0" encoding="windows-1251"?>
<ValCurs Date="27.10.2026" name="Foreign Currency Market">
<Valute ID="R01235"><NumCode>840</NumCode><CharCode>USD</CharCode><Nominal>1</Nominal>
<Name>Доллар США</Name><Value>80,5000</Value></Valute>
<Valute ID="R99999"><NumCode>999</NumCode><CharCode>BAD</CharCode><Nominal>1</Nominal>
<Name>Сломанная</Name><Value>abc</Value></Valute>
</ValCurs>""".encode("windows-1251")


def test_cbr_parse_num_code():
    rates = CbrXmlProvider.parse(SAMPLE_XML)
    assert rates["USD"].num_code == "840"
    assert rates["JPY"].num_code == "392"


def test_cbr_timeout(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.Timeout("долго")

    monkeypatch.setattr(requests, "get", fake_get)
    with pytest.raises(ProviderError, match="не ответил"):
        CbrXmlProvider().get_rates()


def test_skipped_count(monkeypatch):
    rates, skipped = CbrXmlProvider.parse_with_stats(BROKEN_XML)
    assert set(rates) == {"USD"}
    assert skipped == 1

    class FakeResponse:
        content = BROKEN_XML

        def raise_for_status(self):
            pass

    monkeypatch.setattr(requests, "get", lambda *a, **kw: FakeResponse())
    provider = CbrXmlProvider()
    provider.get_rates()
    assert provider.skipped_count == 1
    with pytest.raises(AttributeError):
        provider.skipped_count = 0

def test_json_parse():
    data = {
        "Date": "2026-10-27T11:30:00+03:00",
        "Valute": {
            "JPY": {"NumCode": "392", "CharCode": "JPY", "Nominal": 100,
                    "Name": "Японских иен", "Value": 53.0},
            "BAD": {"CharCode": "BAD"},
        },
    }
    rates = CbrJsonProvider.parse(data)
    assert set(rates) == {"JPY"}
    assert rates["JPY"].per_unit == Decimal("0.53")
    with pytest.raises(ProviderError):
        CbrJsonProvider.parse({})