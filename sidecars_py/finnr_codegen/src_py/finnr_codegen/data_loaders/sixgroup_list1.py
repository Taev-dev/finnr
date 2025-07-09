from __future__ import annotations

from collections.abc import Iterable
from csv import DictReader

from finnr_codegen._types import DATA_DIR
from finnr_codegen._types import CurrencyInfoRow

SRCFILE = DATA_DIR / 'sixgroup_list1(active)-2025-02-04.csv'


def load_sixgroup_list1() -> Iterable[CurrencyInfoRow]:
    with SRCFILE.open(newline='', encoding='utf-8') as csv_file:
        reader = DictReader(csv_file)

        for row in reader:
            # It'd be nice if there were an easy way to apply this to the
            # DictReader instead of doing it over and over again for every
            # row, but since we're only processing a few hundred rows, it
            # doesn't matter
            norm_row: dict[str, str] = {
                key.lower(): value for key, value in row.items()}

            if not _skip_row(norm_row):
                numcode_str = norm_row['numeric code']
                # Remove leading zeroes to prevent accidental octal-ization
                numcode = int(numcode_str.lstrip('0'))

                # We did some ahead-of-time cleanup with this; if we need
                # to regenerate this completely based on source, we should
                # bring it into the codegen source instead of as a formula
                # in a spreadsheet
                if (
                    minor_denom_str := norm_row['minor unit denominator']
                ) == 'continuous':
                    minor_denom = None
                else:
                    minor_denom = int(minor_denom_str)

                yield CurrencyInfoRow(
                    code_alpha3=norm_row['alphabetic code'],
                    code_num=numcode,
                    name=norm_row['currency'],
                    minor_unit_denominator=minor_denom,
                    entity_name=norm_row['entity'],
                    entity_code=None,
                    active_from=None,
                    active_to=None)


def _skip_row(norm_row: dict[str, str]) -> bool:
    """The source data is oriented around entities, but not every entity
    has a currency. Therefore there are a few rows that have empty
    values. We just care about the currencies, so we want to skip those
    rows entirely.
    """
    return (
        norm_row['numeric code'] == ''
        or norm_row['alphabetic code'] == '')
