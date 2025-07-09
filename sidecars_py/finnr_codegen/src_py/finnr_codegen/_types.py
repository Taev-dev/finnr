from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Literal

from whenever import Date
from whenever import YearMonth

from finnr._types import Singleton

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
DATA_DIR = REPO_ROOT / 'src_data'


@dataclass(slots=True)
class CurrencyInfoRow:
    code_alpha3: str | None
    code_num: int | None
    name: str | None = field(compare=False)
    minor_unit_denominator: int | None | Literal[Singleton.UNKNOWN]
    entity_name: str | None = field(compare=False)
    entity_code: str | None = field(compare=False)
    active_from: int | Date | YearMonth | None = field(compare=False)
    active_to: int | Date | YearMonth | None = field(compare=False)
