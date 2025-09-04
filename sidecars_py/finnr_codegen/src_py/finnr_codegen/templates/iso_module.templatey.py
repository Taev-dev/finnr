"""This module contains the ISO-4271 currency database in code form.

> Implementation notes
__style_modifiers__: 'ccw/nodisplay'
    THIS MODULE IS 100% AUTOMATICALLY GENERATED VIA THE CODEGEN SIDECAR
    (See sidecars_py).

    Do not modify it directly.
"""
from datetime import date
from typing import Annotated

from docnote import Note

from finnr._types import Singleton
from finnr.currency import Currency
from finnr.currency import CurrencySet

mint: Annotated[
    CurrencySet,
    Note('The ISO-4217 currency database.')
] = CurrencySet({
␎
slot.currencies:
    __suffix__=',\n'
␏})
