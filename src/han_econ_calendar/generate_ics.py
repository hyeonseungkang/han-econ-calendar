"""
read entire file names in <workspace_dir>/temp/
filter file has '.xls'
group filenames by natcd (parsed from filename)
loop per natcd, loop that natcd's filenames:
    import pandas
    row has columns: 날짜, 시간, 국가, 경제지표, 실제, 예상, 이전, 중요도
    loop row:
        use 날짜, 시간 to define time and date, timezone to GMT so it can import to google calendar
        use 국가, 경제지표 to define schedule name, format: '$경제지표'
        use 실제, 예상, 이전, 중요도 to define schedule body, format '실제: $실제, 예상: $예상, 이전: $이전\n중요도: $중요도'
use vobject so export one ics calendar file per natcd, to <workspace_dir>/serve/<natcd>.ics
"""

import re
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import vobject
from python_calamine import CalamineError
from vobject.icalendar import utc as UTC

from .fetch import TEMP_DIR, WORKSPACE_DIR

SERVE_DIR = WORKSPACE_DIR / "serve"

# fetch.py names files "<year>-<month>_<natcd>.xls"
_FILENAME_RE = re.compile(r"^(?P<year>\d{4})-(?P<month>\d{2})_(?P<natcd>.+)$")
# row dates look like "09.14 (Mon)", no year
_DATE_RE = re.compile(r"(?P<month>\d{2})\.(?P<day>\d{2})")
_REQUIRED_COLUMNS = ["날짜", "시간", "국가", "경제지표", "실제", "예상", "이전", "중요도"]


def _xls_files() -> list[Path]:
    return sorted(p for p in TEMP_DIR.iterdir() if p.suffix == ".xls")


def _event_start(
    date_value: str, time_value: str, year: int, file_month: int
) -> datetime:
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
            event_time = (
                datetime.strptime(time_str, "%H:%M").replace(tzinfo=UTC).time()
            )
        except ValueError as exc:
            raise ValueError(f"unrecognized time: {time_value!r}") from exc
    else:
        event_time = datetime.min.time()
    return datetime.combine(event_date, event_time, tzinfo=UTC)


def _add_event(
    calendar: vobject.base.Component, row: pd.Series, year: int, file_month: int
) -> None:
    event = calendar.add("vevent")
    event.add("dtstart").value = _event_start(
        row["날짜"], row["시간"], year, file_month
    )  # type: ignore[assignment]
    event.add("summary").value = f"{row['경제지표']}"
    event.add(
        "description"
    ).value = f"실제: {row['실제']}, 예상: {row['예상']}, 이전: {row['이전']}, 중요도: {row['중요도']}"


def _files_by_natcd() -> dict[str, list[Path]]:
    by_natcd: defaultdict[str, list[Path]] = defaultdict(list)
    for xls_path in _xls_files():
        match = _FILENAME_RE.match(xls_path.stem)
        if not match:
            continue
        by_natcd[match["natcd"]].append(xls_path)
    return by_natcd


def generate_ics() -> list[Path]:
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
