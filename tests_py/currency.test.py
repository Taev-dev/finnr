from __future__ import annotations

from decimal import Decimal

from finnr._types import Singleton
from finnr.currency import Currency
from finnr.currency import CurrencySet
from finnr.currency import heal_float
from finnr.money import Money


class TestCurrency:

    def test_active(self):
        """is_active must return correct values."""
        currency = Currency(
            code_alpha3='EUR',
            code_num=978,
            minor_unit_denominator=100,
            entities=frozenset(),
            name='Euro',
            approx_active_from=Singleton.UNKNOWN,
            approx_active_until=None,)
        assert currency.is_active

        currency = Currency(
            code_alpha3='EUR',
            code_num=978,
            minor_unit_denominator=100,
            entities=frozenset(),
            name='Euro',
            approx_active_from=Singleton.UNKNOWN,
            approx_active_until=Singleton.UNKNOWN,)
        assert not currency.is_active


class TestCurrencySet:

    def test_minting_plain(self):
        """Minting (calling the currency set) must return a money
        instance.
        """
        mint = CurrencySet({Currency(
            code_alpha3='EUR',
            code_num=978,
            minor_unit_denominator=100,
            entities=frozenset(),
            name='Euro',
            approx_active_from=Singleton.UNKNOWN,
            approx_active_until=None,)})
        result = mint(1, 'EUR')
        assert isinstance(result, Money)
        assert result.amount == Decimal(1)
        assert result.currency.code_alpha3 == 'EUR'

    def test_minting_healing(self):
        """Minting must heal bad floats when they are passed, provided
        the value was True.
        """
        mint = CurrencySet({Currency(
            code_alpha3='EUR',
            code_num=978,
            minor_unit_denominator=100,
            entities=frozenset(),
            name='Euro',
            approx_active_from=Singleton.UNKNOWN,
            approx_active_until=None,)})
        result = mint(3.14, 'EUR')
        assert result.amount == Decimal('3.14')

    def test_minting_quantization_decimal(self):
        """Minting must quantize correctly with decimal currencies when
        quantize_to_minor=True.
        """
        mint = CurrencySet({Currency(
            code_alpha3='EUR',
            code_num=978,
            minor_unit_denominator=100,
            entities=frozenset(),
            name='Euro',
            approx_active_from=Singleton.UNKNOWN,
            approx_active_until=None,)})
        result = mint('3.1415', 'EUR', quantize_to_minor=True)
        assert result.amount == Decimal('3.14')

    def test_minting_quantization_nondecimal(self):
        """Minting must quantize correctly with non-decimal currencies
        when quantize_to_minor=True.
        """
        mint = CurrencySet({Currency(
            code_alpha3='MGA',
            code_num=969,
            minor_unit_denominator=5,
            entities=frozenset(),
            name='Malagasy Ariary',
            approx_active_from=Singleton.UNKNOWN,
            approx_active_until=None,)})
        result = mint('3.1415', 'MGA', quantize_to_minor=True)
        assert result.amount == Decimal('3.2')


def test_heal_float():
    """heal_float must produce expected results.
    TODO: parameterize!
    """
    badfloat = Decimal(3.14)  # noqa: RUF032
    gooddec = Decimal('3.14')
    assert badfloat != gooddec
    assert heal_float(badfloat) == gooddec
