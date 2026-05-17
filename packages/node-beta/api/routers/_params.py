from typing import Annotated
from fastapi import Path, Query

TICKER_PATTERN = r"^[A-Za-z0-9&._-]+$"
TICKER_MIN_LENGTH = 1
TICKER_MAX_LENGTH = 20

TickerPathParam = Annotated[
    str,
    Path(..., min_length=TICKER_MIN_LENGTH, max_length=TICKER_MAX_LENGTH, pattern=TICKER_PATTERN),
]
TickerQueryParam = Annotated[
    str,
    Query(..., min_length=TICKER_MIN_LENGTH, max_length=TICKER_MAX_LENGTH, pattern=TICKER_PATTERN),
]
OptionalTickerQueryParam = Annotated[
    str | None,
    Query(
        None,
        max_length=TICKER_MAX_LENGTH,
        pattern=rf"^$|{TICKER_PATTERN}",
        description="Filter by ticker (optional)",
    ),
]
