from __future__ import annotations

from textwrap import wrap
from typing import Literal

from templatey import Slot
from templatey import Var
from templatey import template
from templatey.prebaked.template_configs import trusted_unicon

from finnr._types import DateLike
from finnr._types import Singleton
from finnr.currency import Currency


@template(trusted_unicon, 'iso_module.templatey.py')
class IsoCurrenciesModuleTemplate:
    currencies: Slot[CurrencyTemplate]


@template(trusted_unicon, 'single_currency.templatey.py')
class CurrencyTemplate:
    code_alpha3: Var[str]
    code_num: Var[int]
    minor_unit_denominator: Var[int | str]
    entities_wrapped: Var[str]
    name: Var[str]
    approx_active_from: Var[str]
    approx_active_until: Var[str]

    @classmethod
    def from_currency(cls, currency: Currency) -> CurrencyTemplate:
        """Converts a currency object into a currency template.
        """
        entities_wrapped = '\n'.join(wrap(
            ', '.join(f"'{entity}'" for entity in sorted(currency.entities)),
            initial_indent='\n            ',
            subsequent_indent='            '))

        approx_active_from = _coerce_datelike_to_str(
            _coerce_singletons_to_str(
                currency.approx_active_from))
        approx_active_until = _coerce_datelike_to_str(
            _coerce_singletons_to_str(
                currency.approx_active_until))

        return cls(
            code_alpha3=currency.code_alpha3,
            code_num=currency.code_num,
            minor_unit_denominator=_coerce_singletons_to_str(
                currency.minor_unit_denominator),
            entities_wrapped=entities_wrapped,
            name=_coerce_singletons_to_str(currency.name),
            approx_active_from=approx_active_from,
            approx_active_until=approx_active_until)


def _coerce_singletons_to_str[T](
        value: T | Literal[Singleton.UNKNOWN] | None
        ) -> T | str:
    if value is Singleton.UNKNOWN:
        return 'Singleton.UNKNOWN'
    elif value is None:
        return 'None'
    else:
        return value


def _coerce_datelike_to_str(value: DateLike | str) -> str:
    if isinstance(value, str):
        return value
    else:
        return f'date({value.year}, {value.month}, {value.day})'
