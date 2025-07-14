"""This module tests the codegen'd moneymath implementation.
Note that it does this by testing on the money class, NOT on the
money math impl protocol!
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from finnr._types import Singleton
from finnr.currency import Currency
from finnr.exceptions import MismatchedCurrency

_test_currency = Currency(
    code_alpha3='EUR',
    code_num=978,
    minor_unit_denominator=100,
    entities=frozenset(),
    name='Euro',
    approx_active_from=Singleton.UNKNOWN,
    approx_active_until=None,)
_other_currency = Currency(
    code_alpha3='MGA',
    code_num=969,
    minor_unit_denominator=5,
    entities=frozenset(),
    name='Malagasy Ariary',
    approx_active_from=Singleton.UNKNOWN,
    approx_active_until=None,)


class TestMoneyMathImpl:
    """This non-exhaustive set of tests is spot-checking misc math
    methods to make sure they produce the expected results.

    We're relying upon codegen to simulate test coverage here, since
    each class of methods was created via the same codegen.

    TODO: parameterize (probably using ``operator``), and possibly reach
    full coverage, regardless of codegen.
    """

    def test_binary_scalars(self):
        """Binary operators requiring a scalar ``other`` must return
        the expected result.
        """
        money1 = _test_currency.mint(100)
        assert money1 * 2 == _test_currency.mint(200)
        assert Decimal('5.5') * money1 == _test_currency.mint(550)
        money1 *= 2
        assert money1 == _test_currency.mint(200)
        money1 /= 2
        assert money1 == _test_currency.mint(100)
        money1 %= 3
        assert money1 == _test_currency.mint(1)

    def test_binary_monies_samecurrency(self):
        """Binary operators requiring a Money ``other`` must return
        the expected result with matching currency.
        """
        money1 = _test_currency.mint(100)
        money2 = _test_currency.mint(50)
        assert money1 + money2 == _test_currency.mint(150)
        assert money1 - money2 == _test_currency.mint(50)
        assert money1.compare(money1) == Decimal(0)
        assert money1.compare(money2) == Decimal(1)

        money1 += money2
        assert money1 == _test_currency.mint(150)
        money1 -= money2
        assert money1 == _test_currency.mint(100)

    def test_binary_monies_wrongcurrency(self):
        """Binary operators requiring a Money ``other`` must return
        the expected result with matching currency.
        """
        money1 = _test_currency.mint(100)
        money2 = _other_currency.mint(50)

        with pytest.raises(MismatchedCurrency):
            _ = money1 + money2
        with pytest.raises(MismatchedCurrency):
            _ = money1 - money2
        with pytest.raises(MismatchedCurrency):
            money1.compare(money2)
        with pytest.raises(MismatchedCurrency):
            money1 += money2

        # Also make sure that the += did nothing, not just that it raised
        assert money1 == _test_currency.mint(100)

    def test_unary(self):
        """Unary operators must return the expected result.
        """
        money1 = _test_currency.mint('100.1')
        assert round(money1) == _test_currency.mint(100)
        assert int(money1) == 100
        assert float(money1) == pytest.approx(100.1)
        money2 = _test_currency.mint('-100')
        assert abs(money2) == _test_currency.mint(100)
        assert -money2 == _test_currency.mint(100)
        assert money2.is_finite()
        assert money2.is_signed()
        assert not money1.is_signed()
        # rosebud
        assert _test_currency.mint(Decimal('inf')).is_infinite()

    def test_overload_samecurrency(self):
        """Overloaded operators must return the expected result for both
        a scalar and a money argument, and must not error with the same
        currency.
        """
        money1 = _test_currency.mint(100)
        assert money1 / 2 == _test_currency.mint(50)
        assert money1 / _test_currency.mint(50) == 2

        assert money1 // 2 == _test_currency.mint(50)
        assert money1 // _test_currency.mint(30) == 3

        # ... I guess these aren't really an overload at this point are they;
        # it could be just ``other: _Scalar | Money -> Money``. Ah well.
        # Hindsight 50/50, not worth the cleanup.
        assert money1 % 30 == _test_currency.mint(10)
        assert money1 % _test_currency.mint(30) == _test_currency.mint(10)
        assert money1.remainder_near(
            _test_currency.mint(30)) == _test_currency.mint(10)
        assert money1.remainder_near(
            _test_currency.mint(60)) == _test_currency.mint(-20)

    def test_overload_wrongcurrency(self):
        """Overloaded operators must raise if passed the wrong currency.
        """
        money1 = _test_currency.mint(100)
        money2 = _other_currency.mint(50)
        with pytest.raises(MismatchedCurrency):
            _ = money1 / money2
        with pytest.raises(MismatchedCurrency):
            _ = money1 // money2
        with pytest.raises(MismatchedCurrency):
            _ = money1 % money2
