"""Independent expanding folds with a common >=25-hour embargo."""

from dataclasses import dataclass
from typing import Iterator

import pandas as pd

from airalerts.grid import _window


@dataclass(frozen=True)
class FoldParams:
    train_start: str = "2025-12-01"
    boundaries: tuple[str, ...] = ("2026-06-01", "2026-06-16", "2026-07-01", "2026-07-16", "2026-08-01")
    test_start: str = "2026-08-01"
    embargo_hours: int = 25


def walk_forward_folds(rows: pd.DataFrame, params: FoldParams, lead: int,
                       final_test: bool = False) -> Iterator[tuple[str, pd.Series, pd.Series]]:
    # Moving a configured TEST date later must not silently waive this stage's
    # reserved August boundary. A final-test invocation is the only waiver.
    limit = min(pd.Timestamp(params.test_start, tz="UTC"), pd.Timestamp(FoldParams().test_start, tz="UTC"))
    boundaries = [pd.Timestamp(b, tz="UTC") for b in params.boundaries]
    if not final_test and any(b > limit for b in boundaries):
        raise ValueError("Evaluation extends into TEST; final_test=True is required")
    train_start = pd.Timestamp(params.train_start, tz="UTC")
    if params.embargo_hours < 25 or params.embargo_hours < lead + 1:
        raise ValueError("Embargo must be >=25 hours and >=lead+1")
    if lead < 0 or len(boundaries) < 2 or train_start >= boundaries[0]:
        raise ValueError("Require nonnegative lead, at least two boundaries, and TRAIN_START before validation")
    if any(b != b.floor("h") for b in boundaries) or train_start != train_start.floor("h"):
        raise ValueError("Split boundaries must be whole UTC hours")
    target_end = rows["T"] + pd.Timedelta(hours=lead + 1)
    available = rows[f"y_{lead}"].notna()
    for i, (start, end) in enumerate(zip(boundaries[:-1], boundaries[1:]), 1):
        _window(start, end)
        train_end = start - pd.Timedelta(hours=params.embargo_hours)
        train = rows["T"].ge(train_start) & rows["T"].lt(train_end) & target_end.le(start) & available
        evaluate = rows["T"].ge(start) & rows["T"].lt(end) & available
        if not final_test:
            evaluate &= target_end.le(limit)
        yield str(i), train, evaluate
