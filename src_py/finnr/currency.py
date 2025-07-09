from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Annotated
from typing import Literal
from typing import overload

from docnote import ClcNote
from whenever import Date
from whenever import YearMonth

from finnr._types import DateLike
from finnr._types import Singleton


@dataclass(slots=True, frozen=True)
class Currency:
    code_alpha3: Annotated[
        str,
        ClcNote('''For all ISO currencies, this is the ISO 4217 alpha-3
            currency code. If implementing custom currencies as part of your
            own ``CurrencySet``, this can be anything you want, but it must
            uniquely identify the currency.''')]

    code_num: Annotated[
        int,
        ClcNote('''For all ISO currencies, this is the ISO 4217 numeric
            currency code. If implementing custom currencies as part of your
            own ``CurrencySet``, this can be anything you want, but it must
            uniquely identify the currency.''')]

    minor_unit_denominator: Annotated[
        int | None | Literal[Singleton.UNKNOWN],
        ClcNote('''The minor unit denominator is used (only) when rounding
            ``Money`` amounts. It determines the minimal fractional unit of
            the currency. For example, with USD or EUR, both of which can be
            broken into 100 cents, it would be 100.

            A value of ``None`` indicates that the currency amounts are
            continuous and cannot be rounded; this is the case with some
            units of account.

            If unknown, then rounding will be a no-op, simply returning a
            copy of the ``Money`` object with the same ``amount``.''')]

    entities: Annotated[
        frozenset[str],
        ClcNote('''For all ISO currencies, this will be a set of strings,
            each containing the ISO 3166 alpha-2 country code. This is
            provided on a best-effort basis, intended primarily for reference,
            and may not be entirely correct.

            If the country no longer exists, it will instead be the 4-letter
            ISO 3166-3 code.

            It may also be empty (for example, for commodities and units of
            account).

            If implementing custom currencies as part of your own
            ``CurrencySet``, this can be truly anything. It is not used
            internally by finnr.''')
        ] = field(compare=False)

    name: Annotated[
        str | Literal[Singleton.UNKNOWN],
        ClcNote('''For all ISO currencies, this is the common name of the
            currency, in English. This is provided on a best-effort basis,
            intended primarily for reference, and may not be entirely correct.

            If implementing custom currencies as part of your own
            ``CurrencySet``, this can be truly anything. It is not used
            internally by finnr.''')
        ] = field(compare=False)

    approx_active_from: Annotated[
        DateLike | Literal[Singleton.UNKNOWN],
        ClcNote('''For all ISO currencies, this is the approximate first date
            of use of the currency. This is provided on a best-effort basis,
            intended primarily for reference, and may not be entirely correct.
            In many cases, the date given may be more precise than the actual
            phase-out of the currency.

            This is used purely to calculate the ``is_active`` property and
            ``was_active_at`` function.

            If implementing custom currencies as part of your own
            ``CurrencySet``, you must set the ``approx_active_from``
            appropriately for the desired behavior of those two properties.''')
        ] = field(compare=False)

    approx_active_until: Annotated[
        DateLike | Literal[Singleton.UNKNOWN] | None,
        ClcNote('''For all ISO currencies, this is the approximate last date
            of use of the currency. This is provided on a best-effort basis,
            intended primarily for reference, and may not be entirely correct.
            In many cases, the date given may be more precise than the actual
            phase-out of the currency.

            This is used purely to calculate the ``is_active`` property and
            ``was_active_at`` function.

            If implementing custom currencies as part of your own
            ``CurrencySet``, you must set the ``approx_active_until``
            appropriately for the desired behavior of those two properties.''')
        ] = field(compare=False)

    @property
    def is_active(self) -> bool:
        raise NotImplementedError

    def was_active_at(self, date: DateLike) -> bool:
        raise NotImplementedError


class CurrencySet(frozenset[Currency]):
    # TODO: think about having additional methods for finding, for example,
    # based on the underlying entity

    @overload
    def get(self, code_alpha3: str, default=None) -> Currency | None: ...
    @overload
    def get(self, code_num: int, default=None) -> Currency | None: ...
