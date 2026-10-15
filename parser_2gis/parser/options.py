from __future__ import annotations

import os

from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt, PositiveInt

from ..chrome.options import default_memory_limit
from ..common import floor_to_hundreds


def default_max_records() -> int:
    """Try linear approximation for optimal max records."""
    max_records = floor_to_hundreds((550 * default_memory_limit() / 1024 - 400))
    return max_records if max_records > 0 else 1


class ParserOptions(BaseModel):
    """Represent all possible options for Parser.

    Attrubutes:
        skip_404_response: Whether to skip 404 document response or not.
        delay_between_clicks: Delay between each item's click in milliseconds.
        max_records: Max number of records to parse from one URL.
        use_gc: Use Garbage Collector.
        gc_pages_interval: Run Garbage Collector every N pages (if `use_gc` enabled).
        api_key: Optional official 2GIS Places API key. It is deliberately
            excluded from serialization so it is never written to config or
            history files.
    """
    model_config = ConfigDict(validate_assignment=True)

    skip_404_response: bool = True
    # A conservative default keeps requests human-paced and avoids needless
    # load. Advanced CLI users can still explicitly choose another value.
    delay_between_clicks: NonNegativeInt = 750
    max_records: PositiveInt = default_max_records()
    use_gc: bool = False
    gc_pages_interval: PositiveInt = 10
    api_key: str = Field(
        default_factory=lambda: os.getenv('PARSER2GIS_API_KEY', ''),
        exclude=True,
        repr=False,
    )
