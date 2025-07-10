from __future__ import annotations

import calendar
import logging
from collections import defaultdict
from dataclasses import replace as dc_replace
from typing import Literal
from typing import cast

import pycountry
from whenever import Date
from whenever import YearMonth

from finnr._types import Singleton
from finnr.currency import Currency

from finnr_codegen._types import CurrencyInfoRow
from finnr_codegen.data_loaders.sixgroup_list1 import load_sixgroup_list1
from finnr_codegen.data_loaders.sixgroup_list3 import load_sixgroup_list3
from finnr_codegen.data_loaders.wiki_iso4217 import load_wiki_iso4217

logger = logging.getLogger(__name__)

HARDCODED_ENTITIES = {
    'european union': 'EU',
    # These are all things where pycountry trips up with no matches
    'virgin islands (british)': 'VG',
    'virgin islands (u.s.)': 'VI',
    'micronesia (federated states of)': 'FM',
    'bolivia (plurinational state of)': 'BO',
    'congo (the democratic republic of the)': 'CD',
    'falkland islands  [malvinas]': 'FK',
    'korea (the democratic people’s republic of)': 'KP',  # noqa: RUF001
    'korea (the republic of)': 'KR',
    'lao people’s democratic republic': 'LA',  # noqa: RUF001
    'moldova (the republic of)': 'MD',
    # WE ARE NOT THE REASON THIS IS HERE. This is coming from the sixgroup
    # data. We don't want to make a statement about the geopolitics of Taiwan
    # here! We just need the country code.
    'taiwan (province of china)': 'TW',
    'international monetary fund (imf)':
        Singleton.MISSING,
    'member countries of the african development bank group':
        Singleton.MISSING,
    'sistema unitario de compensacion regional de pagos "sucre"':
        Singleton.MISSING,
    # These have multiple fuzzy matches without an exact name match
    'niger': 'NE',
    # These are historical ones that also tripped up pycountry. Again, they
    # aren't here because we're endorsing anything, they're here because we
    # need to normalize data, and we literally can't change what exists in
    # the data we're getting without doing this!
    'french  guiana': 'GF',
    # bumm. niiiice.
    'burma': 'BUMM',
    'czechoslovakia': 'CSHH',
    'european monetary co-operation fund (emcf)': Singleton.MISSING,
    'german democratic republic': 'DDDE',
    'lao': 'LAO',
    'netherlands antilles': 'ANHH',
    'serbia and montenegro': 'CSXX',
    'southern rhodesia': 'RHZW',
    # Since 2018, known by the (IMO quite aesthetically pleasing) name Eswatini
    'swaziland': 'SZ',
    'turkey': 'TR',
    'union of soviet socialist republics': 'SUHH',
    'yemen, democratic': 'YDYE',
    'yugoslavia': 'YUCS',
}


def fuse_src_data() -> dict[str, Currency]:
    list1_infos: dict[str, list[CurrencyInfoRow]] = defaultdict(list)
    list3_infos: dict[str, list[CurrencyInfoRow]] = defaultdict(list)
    wiki_4217_infos: dict[str, list[CurrencyInfoRow]] = defaultdict(list)

    for info_row in load_sixgroup_list1():
        if info_row.code_alpha3 is not None:
            list1_infos[info_row.code_alpha3].append(info_row)
        else:
            logger.warning(
                'Discarding list1 row with missing alpha3: %s', info_row)
    for info_row in load_sixgroup_list3():
        if info_row.code_alpha3 is not None:
            list3_infos[info_row.code_alpha3].append(info_row)
        else:
            logger.warning(
                'Discarding list3 row with missing alpha3: %s', info_row)
    for info_row in load_wiki_iso4217():
        if info_row.code_alpha3 is not None:
            wiki_4217_infos[info_row.code_alpha3].append(info_row)
        else:
            logger.warning(
                'Discarding wiki4217 row with missing alpha3: %s', info_row)

    fused: list[Currency] = []
    # Order here is important for deduplication!
    fused.extend(_fuse_active_currencies(list1_infos))
    fused.extend(_fuse_historical_currencies(list3_infos, wiki_4217_infos))

    # Note that, because the six group data is oriented towards ENTITIES and
    # not currencies, there are some currencies (ex EUR) that appear in both
    # historical and active data (because the entity ceased to exist, ex CSXX).
    deduped: dict[str, Currency] = {}
    # Note that, for the dates to be correct, this relies upon the ordering
    # of the calls to fuse.
    for currency in fused:
        if currency.code_alpha3 in deduped:
            existing_currency = deduped[currency.code_alpha3]
            deduped[currency.code_alpha3] = dc_replace(
                existing_currency,
                entities=frozenset(
                    existing_currency.entities | currency.entities))
        else:
            deduped[currency.code_alpha3] = currency

    return deduped


def _fuse_active_currencies(
        list1_infos: dict[str, list[CurrencyInfoRow]]
        ) -> list[Currency]:
    excs: list[Exception] = []
    results: list[Currency] = []
    for code_alpha3, info_rows in list1_infos.items():
        if any(info_row != info_rows[0] for info_row in info_rows):
            raise ValueError(
                'Inconsistent currency info from list1!', info_rows)

        info = info_rows[0]
        if info.code_num is None:
            logger.warning(
                'Discarding list1 row with missing numcode: %s', info)
            continue

        entity_names = {info_row.entity_name for info_row in info_rows}
        entity_names.discard(None)
        entity_names = cast(set[str], entity_names)

        # We really, really want to group ALL of these together until we get
        # to the very end, otherwise hardcoding them takes FOREVER.
        try:
            entities = frozenset(_get_entity_codes(entity_names))
        except ValueError as exc:
            excs.append(exc)
            continue

        if info.name is None:
            name = Singleton.UNKNOWN
        else:
            name = info.name

        results.append(Currency(
            code_alpha3=code_alpha3,
            code_num=info.code_num,
            minor_unit_denominator=info.minor_unit_denominator,
            entities=entities,
            name=name,
            approx_active_from=Singleton.UNKNOWN,
            approx_active_until=None
            ))

    # We're going to just consolidate all of the exception notes into a
    # single exception. The cleaner way would be for _get_entity_codes to
    # return an error list, but... well we already wrote the code; we can
    # clean it up later if it becomes a maintenance issue -- this isn't part
    # of the distributed package!
    if excs:
        exc0 = excs[0]
        for exc in excs[1:]:
            for note in exc.__notes__:
                exc0.add_note(note)
        raise exc0

    return results


def _fuse_historical_currencies(
        list3_infos: dict[str, list[CurrencyInfoRow]],
        wiki_4217_infos: dict[str, list[CurrencyInfoRow]]
        ) -> list[Currency]:
    exc_notes: list[str] = []
    results: list[Currency] = []

    for code_alpha3, info_rows in list3_infos.items():
        if any(info_row != info_rows[0] for info_row in info_rows):
            raise ValueError(
                'Inconsistent currency info from list3!', info_rows)

        # Note: wikipedia has no duplicates; we don't need to worry about it.
        # It also doesn't include entity information.
        sixgroup_info = info_rows[0]
        wiki_info = wiki_4217_infos.get(code_alpha3, [CurrencyInfoRow(
            code_alpha3=code_alpha3,
            code_num=None,
            name=None,
            minor_unit_denominator=Singleton.UNKNOWN,
            entity_name=None,
            entity_code=None,
            active_from=None,
            active_to=None)])[0]

        code_num = sixgroup_info.code_num or wiki_info.code_num
        if code_num is None:
            logger.warning(
                'Discarding list3 row with missing numcode: %s', sixgroup_info)
            continue

        entity_names = {info_row.entity_name for info_row in info_rows}
        entity_names.discard(None)
        entity_names = cast(set[str], entity_names)

        # We really, really want to group ALL of these together until we get
        # to the very end, otherwise hardcoding them takes FOREVER.
        try:
            entities = frozenset(_get_entity_codes(entity_names))
        except ValueError as exc:
            exc_notes.extend(exc.__notes__)
            continue

        name = _get_best_name(sixgroup_info.name, wiki_info.name)
        # Goal here for coercion: maximize the possible range (be as
        # conservative as possible)
        approx_active_from = _get_best_date(
            # For from, we want the earliest part of the window, == 1
            # Also note: we're preferring the wiki dates here, as long as
            # they're at least or more precise than sixgroup. Hence the
            # reversed order. Rationale: wikipedia tends to be pretty good
            # for historiography
            wiki_info.active_from, None, 1)
        approx_active_until = _get_best_date(
            # For until, we want the latest part of the window, == -1
            # Also note: we're preferring the wiki dates here, as long as
            # they're at least or more precise than sixgroup. Hence the
            # reversed order. Rationale: wikipedia tends to be pretty good
            # for historiography
            wiki_info.active_to, sixgroup_info.active_to, -1)

        results.append(Currency(
            code_alpha3=code_alpha3,
            code_num=code_num,
            minor_unit_denominator=wiki_info.minor_unit_denominator,
            entities=entities,
            name=name,
            approx_active_from=approx_active_from,
            approx_active_until=approx_active_until
            ))

    if exc_notes:
        exc = ValueError('Failed to fuse historical currencies!')
        for exc_note in exc_notes:
            exc.add_note(exc_note)
        raise exc

    return results


def _get_best_date(
        date1: int | Date | YearMonth | None,
        date2: int | Date | YearMonth | None,
        fill_direction: Literal[-1] | Literal[1]
        ) -> Date | Literal[Singleton.UNKNOWN]:
    """Note that, in the case equal quality, we prefer date1.
    """
    if date1 is not None and date2 is not None:
        date1_quality, date1_coercion = _coerce_date(date1, fill_direction)
        date2_quality, date2_coercion = _coerce_date(date2, fill_direction)

        if date1_quality >= date2_quality:
            return date1_coercion
        else:
            return date2_coercion

    elif date1 is not None:
        return _coerce_date(date1, fill_direction)[1]

    elif date2 is not None:
        return _coerce_date(date2, fill_direction)[1]

    return Singleton.UNKNOWN


def _coerce_date(
        date: int | Date | YearMonth,
        fill_direction: Literal[-1] | Literal[1]
        ) -> tuple[int, Date]:
    """Returns a tuple of (quality, coerced date). Choose the value with
    the highest quality.

    Fill direction must be +1 or -1. +1 will be the first of the
    month/year, -1 the end (just like with slicing).
    """
    if isinstance(date, int):
        if fill_direction == 1:
            return (0, Date(date, 1, 1))
        else:
            return (0, Date(date, 12, 31))

    elif isinstance(date, YearMonth):
        if fill_direction == 1:
            return (1, date.on_day(1))
        else:
            __, last_day = calendar.monthrange(date.year, date.month)
            return (1, date.on_day(last_day))

    else:
        return (2, date)


def _get_best_name(
        name1: str | None,
        name2: str | None,
        ) -> str | Literal[Singleton.UNKNOWN]:
    """Note that this always has a preference for name1! If both are
    defined, it doesn't do any heuristics or anything, it just chooses
    name1.
    """
    if name1 is not None and name2 is not None:
        return name1

    elif name1 is not None:
        return name1

    elif name2 is not None:
        return name2

    return Singleton.UNKNOWN


def _get_entity_codes(entity_names: set[str]) -> set[str]:  # noqa: C901, PLR0912
    """Uses pycountry (and extra hard-coding coercion logic) to convert
    all of our entity names into ISO alpha2 codes.
    """
    failures = []
    results = set()
    for entity_name in entity_names:
        # In addition to just making things cleaner, leaving it out also messes
        # up pycountry
        normalized_name = entity_name.replace('(THE)', '').strip().lower()
        hardcoded_entity = HARDCODED_ENTITIES.get(normalized_name)
        if hardcoded_entity is not None:
            if hardcoded_entity is not Singleton.MISSING:
                results.add(hardcoded_entity)

            continue

        # This is a european unit of account not used by any entities, or a
        # testing code
        if 'zz0' in normalized_name or 'zz1' in normalized_name:
            continue

        fuzzies = []
        try:
            fuzzies.extend(pycountry.countries.search_fuzzy(normalized_name))
        except LookupError:
            pass

        # Flip around the parens, if any are around.
        if '(' in normalized_name:
            first_part, _, second_part = normalized_name.partition('(')
            normalized_name_alt = (
                f"{second_part.replace(')', '')} {first_part}")
            try:
                fuzzies.extend(pycountry.countries.search_fuzzy(
                    normalized_name_alt))
            except LookupError:
                pass

        if len(fuzzies) == 1:
            results.add(fuzzies[0].alpha_2)

        # (The same) typing bug in pycountry
        elif fuzzies:  # type: ignore
            for fuzzy in fuzzies:
                if (
                    fuzzy.name.lower() == normalized_name
                    # Evidently this doesn't always exist? Or the fuzzy matches
                    # aren't actually the same objects? It's very... strange.
                    or getattr(fuzzy, 'official_name', '').lower()
                    == normalized_name
                ):
                    results.add(fuzzies[0].alpha_2)
                    break
            else:
                failures.append((entity_name, normalized_name, fuzzies))

        else:
            failures.append((entity_name, normalized_name, fuzzies))
            continue

    # Waaay better to do this all at once than need to do it one at a time!
    if failures:
        exc = ValueError(
            'Non-hardcoded, non-singular entity name fuzzy match(es)')
        for entity_name, normalized_name, fuzzies in failures:
            exc.add_note(f'  {entity_name} (``{normalized_name}``: {fuzzies=}')
        raise exc

    return results
