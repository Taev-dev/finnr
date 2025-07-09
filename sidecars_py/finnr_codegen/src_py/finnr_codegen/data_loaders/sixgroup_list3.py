from __future__ import annotations

import re
from collections.abc import Iterable
from csv import DictReader

from whenever import Date
from whenever import YearMonth

from finnr._types import Singleton

from finnr_codegen._types import DATA_DIR
from finnr_codegen._types import CurrencyInfoRow

SRCFILE = DATA_DIR / 'sixgroup_list3(historical)-2025-02-04.csv'
YEAR_RANGE_PATTERN = re.compile(
    r'^\s*[0-9]{4}( to |\-)(?P<endpoint>[0-9]{4})\s*$')
YEARMONTH_RANGE_PATTERN = re.compile(
    r'^\s*[0-9]{4}\-[0-9]{2} to (?P<endpoint>[0-9]{4}\-[0-9]{2})\s*$')


def load_sixgroup_list3() -> Iterable[CurrencyInfoRow]:
    with SRCFILE.open(newline='', encoding='utf-8') as csv_file:
        reader = DictReader(csv_file)

        for row in reader:
            # It'd be nice if there were an easy way to apply this to the
            # DictReader instead of doing it over and over again for every
            # row, but since we're only processing a few hundred rows, it
            # doesn't matter
            norm_row: dict[str, str] = {
                key.lower(): value for key, value in row.items()}

            numcode_str = norm_row['numeric code']
            if numcode_str:
                # Remove leading zeroes to prevent accidental octal-ization
                numcode = int(numcode_str.lstrip('0'))
            else:
                numcode = None

            yield CurrencyInfoRow(
                code_alpha3=norm_row['alphabetic code'],
                code_num=numcode,
                name=norm_row['historic currency'],
                minor_unit_denominator=Singleton.UNKNOWN,
                entity_name=norm_row['entity'],
                entity_code=None,
                # The data for both of these two is both too dirty (mix of
                # years, year with month, year ranges, and year-with-month
                # ranges) and too coarse, so... just skip it
                active_from=None,
                active_to=_coerce_date(norm_row['withdrawal date']))


def _coerce_date(date_str: str) -> int | Date | YearMonth | None:
    """This is just a bunch of hand-written logic to clean up the
    wikipedia dates as much as possible.

    This is a best-effort kind of thing. If we can't get something
    reasonable, we'll return None.

    When a range is given, we always go for the endpoint of the range.
    """
    if not date_str:
        return None

    if (range_match := YEAR_RANGE_PATTERN.match(date_str)) is not None:
        endpoint = range_match.group('endpoint')
        return int(endpoint)

    if (range_match := YEARMONTH_RANGE_PATTERN.match(date_str)) is not None:
        endpoint = range_match.group('endpoint')
        return YearMonth.parse_common_iso(endpoint)

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
