from __future__ import annotations

import re
from collections.abc import Iterable
from csv import DictReader

from whenever import Date
from whenever import YearMonth

from finnr._types import Singleton

from finnr_codegen._types import DATA_DIR
from finnr_codegen._types import CurrencyInfoRow

SRCFILE = DATA_DIR / 'wikipedia_iso4271(historical)-2025-02-21.csv'
FOOTNOTE_PATTERN = re.compile(r'\[[A-z0-9]+?\]')
UNKNOWN_DENOM_PATTERN = re.compile(r'^\s*[\.]*\s*$')


def load_wiki_iso4217() -> Iterable[CurrencyInfoRow]:
    with SRCFILE.open(newline='', encoding='utf-8') as csv_file:
        reader = DictReader(csv_file)

        for row in reader:
            # It'd be nice if there were an easy way to apply the .lower to the
            # DictReader instead of doing it over and over again for every
            # row, but since we're only processing a few hundred rows, it
            # doesn't matter
            norm_row: dict[str, str] = {
                FOOTNOTE_PATTERN.sub('', key.lower()):
                    FOOTNOTE_PATTERN.sub('', value)
                for key, value in row.items()}

            try:
                numcode = int(norm_row['num'])
            except ValueError:
                numcode = None

            if UNKNOWN_DENOM_PATTERN.match(
                minor_denom_str := norm_row['d']
            ) is None:
                minor_denom_exp = int(minor_denom_str)
                minor_denom = 10 ** minor_denom_exp
            else:
                minor_denom = Singleton.UNKNOWN

            yield CurrencyInfoRow(
                code_alpha3=norm_row['code'],
                code_num=numcode,
                name=norm_row['currency'],
                minor_unit_denominator=minor_denom,
                entity_name=None,
                entity_code=None,
                active_from=_coerce_date(norm_row['from']),
                active_to=_coerce_date(norm_row['until']))


def _coerce_date(date_str: str) -> int | Date | YearMonth | None:
    """This is just a bunch of hand-written logic to clean up the
    wikipedia dates as much as possible.

    This is a best-effort kind of thing. If we can't get something
    reasonable, we'll return None.
    """
    if not date_str:
        return None

    try:
        return Date.parse_common_iso(date_str)
    except ValueError:
        try:
            return int(date_str)
        except ValueError:
            pass

    try:
        return YearMonth.parse_common_iso(date_str)
    except ValueError:
        pass
