"""THIS MODULE IS 100% AUTOMATICALLY GENERATED VIA THE CODEGEN SIDECAR
(See sidecars_py).

Do not modify it directly.

Some notes:
++  We want to strictly separate the codegen from any custom
    implementation as part of the ``Money`` object, so this module
    contains ONLY money math.
++  The circular injection of ``Money`` is simply the most performant
    way to access the Money object.
++  Note that decimal doesn't implement augmented operations; therefore,
    we have to be careful to reference the non-augmented methods within
    the template
++  There are some things that are marked as overloads that could have
    been converted into a separate template for unions, since they
    aren't actually overloads (eg ``__mod__``), but rather,
    ``other: _Scalar | Money -> Money``. These used to be actual
    overloads, but I changed them when I realized they didn't make any
    sense like that. Might be worth cleaning them up later, but for now,
    it's not hurting anything.
"""
from __future__ import annotations

import typing
from decimal import Context
from decimal import Decimal
from typing import Protocol
from typing import Self
from typing import overload

from finnr.exceptions import MismatchedCurrency
from finnr.exceptions import MoneyRequired
from finnr.exceptions import ScalarRequired

if typing.TYPE_CHECKING:
    from finnr.currency import Currency

    # Note: at runtime, this gets injected by the money module itself, so
    # that the value is available at runtime
    from finnr.money import Money

type _Scalar = Decimal | int


class MoneyMathImpl(Protocol):
    amount: Decimal
    currency: Currency

    def __init__(self, amount: Decimal, currency: Currency): ...

    ###########################################################
    # These are all dynamically codegen'd
    ###########################################################␎
    slot.methods: __prefix__='\n\n'␏

    ###########################################################
    # The rest of the math methods are unique and special-cased
    # (but still created within codegen)
    ###########################################################

    @overload
    def __divmod__(self, other: Money) -> tuple[Decimal, Money]: ...
    @overload
    def __divmod__(self, other: Decimal | int) -> tuple[Money, Money]: ...
    def __divmod__(
            self,
            other: Decimal | int | Money
            ) -> tuple[Decimal | Money, Money]:
        if isinstance(other, Money):
            if self.currency != other.currency:
                raise MismatchedCurrency(self.currency, other.currency)

            quotient, remainder = self.amount.__divmod__(other.amount)
            return quotient, Money(amount=remainder, currency=self.currency)

        else:
            quotient, remainder = self.amount.__divmod__(other)
            return (
                Money(amount=quotient, currency=self.currency),
                Money(amount=remainder, currency=self.currency))

    def adjusted(self) -> int:
        return self.amount.adjusted()

    def fma(
            self,
            other: Decimal | int,
            third: Money,
            context=None
            ) -> Money:
        if self.currency != third.currency:
            raise MismatchedCurrency(self.currency, third.currency)

        return Money(
            amount=self.amount.fma(other, third.amount),
            currency=self.currency)

    # Note: special-cased because of the rounding argument
    def quantize(
            self,
            exp: Decimal | int | Money,
            rounding: str | None = None,
            context: Context | None = None,
            ) -> Money:
        if isinstance(exp, Money):
            if self.currency != exp.currency:
                raise MismatchedCurrency(self.currency, exp.currency)

            return Money(
                amount=self.amount.quantize(
                    exp.amount,
                    rounding=rounding,
                    context=context),
                currency=self.currency)

        else:
            return Money(
                amount=self.amount.quantize(
                    exp,
                    rounding=rounding,
                    context=context),
                currency=self.currency)
