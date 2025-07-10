from __future__ import annotations

import typing
from dataclasses import dataclass
from decimal import ROUND_HALF_UP
from decimal import Decimal

if typing.TYPE_CHECKING:
    from finnr.currency import Currency


@dataclass(slots=True)
class Money:
    """Note that this might be theoretically nonsensical, for
    example, including fractional cents of the USD. This can be
    rounded either fractionally or decimally via the associated
    methods.
    """
    amount: Decimal
    currency: Currency

    def round_to_decimal(self, rounding=ROUND_HALF_UP) -> Money: ...
    def round_to_major(self, rounding=ROUND_HALF_UP) -> Money: ...
    def round_to_minor(self, rounding=ROUND_HALF_UP) -> Money: ...

    @property
    def is_nominal_division(self) -> bool: ...
        # Returns whether or not the amount can be expressed as an
        # integer multiple of the minor unit

    @property
    def is_nominal_major(self) -> bool: ...
        # Returns whether or not the amount can be expressed as an
        # integer multiple of the major unit

    def __add__(self, other) -> Money: ...
    # etc
