"""Convert fetched ``.xls`` exports into per-nation iCalendar files.

Every ``.xls`` file directly under ``DATA_DIR`` (named
``<year>-<month>_<natcd>.xls`` by ``fetch.py``) is read with columns
날짜 (date), 시간 (time), 국가 (nation), 경제지표 (indicator), 실제 (actual),
예상 (forecast), 이전 (previous), and 중요도 (importance). Files are grouped
by ``natcd``, and for each group every row becomes one ``VEVENT``:

- ``dtstart`` is built from 날짜/시간, resolved against the file's
  ``<year>-<month>`` (with a rollover for dates near a year boundary) and
  expressed in UTC.
- ``summary`` is the indicator name (경제지표).
- ``description`` is ``실제: ..., 예상: ..., 이전: ...`` followed by
  ``중요도: ...`` on its own line.

One ``vobject`` iCalendar is written per ``natcd`` to
``<workspace_dir>/serve/<natcd>.ics``.
"""

import re
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import vobject
from python_calamine import CalamineError
from vobject.icalendar import utc as UTC

from .fetch import DATA_DIR, WORKSPACE_DIR

SERVE_DIR = WORKSPACE_DIR / "serve"

# fetch.py names files "<year>-<month>_<natcd>.xls"
_FILENAME_RE = re.compile(r"^(?P<year>\d{4})-(?P<month>\d{2})_(?P<natcd>.+)$")
# row dates look like "09.14 (Mon)", no year
_DATE_RE = re.compile(r"(?P<month>\d{2})\.(?P<day>\d{2})")
_REQUIRED_COLUMNS = [
    "날짜",
    "시간",
    "국가",
    "경제지표",
    "실제",
    "예상",
    "이전",
    "중요도",
]


def _xls_files() -> list[Path]:
    """List every ``.xls`` file directly under ``DATA_DIR``, sorted by name."""
    return sorted(p for p in DATA_DIR.iterdir() if p.suffix == ".xls")


def _event_start(
    date_value: str, time_value: str, year: int, file_month: int
) -> datetime:
    """Resolve one row's 날짜/시간 into a timezone-aware UTC event start.

    ``date_value`` carries no year (e.g. ``"09.14 (Mon)"``), so it is
    resolved against ``year``/``file_month`` (the file's own year and
    month). If the row's month is more than 6 months away from
    ``file_month``, ``year`` is rolled to the adjacent year, to handle
    rows near a December/January boundary.

    Args:
        date_value: Raw 날짜 cell, formatted ``MM.DD (Day)``.
        time_value: Raw 시간 cell, formatted ``HH:MM``, or empty/blank for
            an all-day event (midnight is used).
        year: The source file's year, from its filename.
        file_month: The source file's month, from its filename.

    Returns:
        The event start as a UTC ``datetime``.

    Raises:
        ValueError: If ``date_value`` or a non-empty ``time_value`` does
            not match the expected format.
    """
    match = _DATE_RE.match(str(date_value).strip())
    if not match:
        raise ValueError(f"unrecognized date: {date_value!r}")
    month = int(match["month"])
    day = int(match["day"])

    # dates near a month's edges can belong to the year before/after the file's year
    if month - file_month > 6:
        year -= 1
    elif file_month - month > 6:
        year += 1

    event_date = date(year, month, day)
    time_str = str(time_value).strip()
    if time_str:
        try:
            event_time = datetime.strptime(time_str, "%H:%M").replace(tzinfo=UTC).time()
        except ValueError as exc:
            raise ValueError(f"unrecognized time: {time_value!r}") from exc
    else:
        event_time = datetime.min.time()
    return datetime.combine(event_date, event_time, tzinfo=UTC)


def _add_event(
    calendar: vobject.base.Component, row: pd.Series, year: int, file_month: int
) -> None:
    """Append one ``VEVENT`` built from a single row to ``calendar`` in place.

    Args:
        calendar: The ``vobject`` iCalendar component to add the event to.
        row: A row from the parsed ``.xls`` dataframe; must contain the
            columns in ``_REQUIRED_COLUMNS``.
        year: The source file's year, passed through to :func:`_event_start`.
        file_month: The source file's month, passed through to
            :func:`_event_start`.
    """
    event = calendar.add("vevent")
    event.add("dtstart").value = _event_start(
        row["날짜"], row["시간"], year, file_month
    )  # type: ignore[assignment]
    event.add("summary").value = f"{row['경제지표']}"
    event.add(
        "description"
    ).value = f"실제: {row['실제']}, 예상: {row['예상']}, 이전: {row['이전']}, 중요도: {row['중요도']}"


def _files_by_natcd() -> dict[str, list[Path]]:
    """Group every ``.xls`` file under ``DATA_DIR`` by the natcd in its filename.

    Files whose stem does not match ``_FILENAME_RE`` are silently skipped.

    Returns:
        A mapping of natcd to its matching file paths, in the sorted order
        returned by :func:`_xls_files`.
    """
    by_natcd: defaultdict[str, list[Path]] = defaultdict(list)
    for xls_path in _xls_files():
        match = _FILENAME_RE.match(xls_path.stem)
        if not match:
            continue
        by_natcd[match["natcd"]].append(xls_path)
    return by_natcd


def generate_ics() -> list[Path]:
    """Build one iCalendar per natcd from ``DATA_DIR`` and write it to ``SERVE_DIR``.

    See the module docstring for the row-to-event mapping.

    Returns:
        The path of every ``.ics`` file written, one per natcd.

    Raises:
        RuntimeError: If a file's data can't be parsed as ``.xls``, is
            missing a required column, or its filename doesn't match the
            ``<year>-<month>_<natcd>.xls`` pattern used by :func:`_xls_files`.
    """
    SERVE_DIR.mkdir(parents=True, exist_ok=True)

    ics_paths = []
    for natcd, xls_paths in _files_by_natcd().items():
        calendar = vobject.iCalendar()

        for xls_path in xls_paths:
            match = _FILENAME_RE.match(xls_path.stem)
            if match is None:
                raise RuntimeError(f"Unexpected filename: {xls_path}")
            year, file_month = int(match["year"]), int(match["month"])

            try:
                df = pd.read_excel(xls_path, dtype=str, engine="calamine").fillna("")
            except CalamineError as err:
                raise RuntimeError(f"Not parsable: {xls_path}") from err
            missing_columns = [c for c in _REQUIRED_COLUMNS if c not in df.columns]
            if missing_columns:
                raise RuntimeError(f"{xls_path} missing columns: {missing_columns}")
            for _, row in df.iterrows():
                _add_event(calendar, row, year, file_month)

        ics_path = SERVE_DIR / f"{natcd}.ics"
        ics_path.write_text(calendar.serialize())
        ics_paths.append(ics_path)

    return ics_paths


if __name__ == "__main__":
    for path in generate_ics():
        print(f"saved {path}")
