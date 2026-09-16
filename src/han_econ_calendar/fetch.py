"""Download raw economic-calendar exports from asp.zeroin.co.kr.

Configuration (``FETCH_BASE_URL``, ``FETCH_QUERY_FORMAT``,
``FETCH_QUERY_STR_NATION_CANDIDATE``, ``FETCH_QUERY_STR_NATCD_CANDIDATE``) is
read from the environment, falling back to the ``.env`` file at the
workspace root. The nation/natcd candidate lists are ``|``-delimited and
position-matched: entry ``i`` of each list describes the same nation.

For every nation and every calendar month spanning last year, this year,
and next year, one export is downloaded and saved to
``<workspace_dir>/data/<year>-<month>_<natcd>.xls``. Months strictly before
the current month are treated as final: if a file for that month already
exists, it is reused instead of re-downloaded. The current month and any
future months are always re-downloaded, since their data can still change.
"""

import calendar
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path
from string import Template
from typing import NamedTuple

WORKSPACE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = WORKSPACE_DIR / ".env"
DATA_DIR = WORKSPACE_DIR / "data"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class MonthRange(NamedTuple):
    """Inclusive calendar-month date range, e.g. 2025-01-01 to 2025-01-31."""

    start: date
    end: date


class NationQuery(NamedTuple):
    """Per-nation query parameters derived from the env candidate lists."""

    natcd: str
    """Short nation code, e.g. ``"kr"``. Used as the output filename suffix."""
    str_nation: str
    """URL-encoded ``english,korean`` name pair for the ``str_nation`` query param."""
    str_natcd: str
    """URL-encoded nation code for the ``str_natcd`` query param."""


def _load_env_file(path: Path) -> None:
    """Load ``KEY=VALUE`` lines from ``path`` into ``os.environ``.

    Existing environment variables are not overridden (see
    ``os.environ.setdefault``). Blank lines and lines starting with ``#``
    are skipped. Does nothing if ``path`` does not exist.

    Args:
        path: Path to an ``.env``-style file.
    """
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _month_ranges() -> list[MonthRange]:
    """Build one date range per calendar month, last year through next year.

    Returns:
        A ``MonthRange(start, end)`` for every month (Jan-Dec) of
        ``this_year - 1``, ``this_year``, and ``this_year + 1``, in that
        order. ``this_year`` is resolved from the local system clock.
    """
    this_year = datetime.now().astimezone().year
    return [
        MonthRange(
            date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])
        )
        for year in (this_year - 1, this_year, this_year + 1)
        for month in range(1, 13)
    ]


def _nations() -> list[NationQuery]:
    """Parse the nation/natcd candidate env vars into per-nation queries.

    ``FETCH_QUERY_STR_NATION_CANDIDATE`` and ``FETCH_QUERY_STR_NATCD_CANDIDATE``
    are ``|``-delimited lists, matched by position; each nation entry in the
    former must be an ``english,korean`` comma pair.

    Returns:
        One ``NationQuery`` per candidate entry, in the same order as the
        env vars.

    Raises:
        ValueError: If the two candidate lists have different lengths, or
            a nation entry is not a single comma-separated pair.
    """
    nation_candidates = os.environ["FETCH_QUERY_STR_NATION_CANDIDATE"].split("|")
    natcd_candidates = os.environ["FETCH_QUERY_STR_NATCD_CANDIDATE"].split("|")

    if len(nation_candidates) != len(natcd_candidates):
        raise ValueError(
            "FETCH_QUERY_STR_NATION_CANDIDATE and FETCH_QUERY_STR_NATCD_CANDIDATE "
            "must have the same number of entries"
        )

    nations: list[NationQuery] = []
    for nation_pair, natcd in zip(nation_candidates, natcd_candidates, strict=True):
        parts = nation_pair.split(",")
        if len(parts) != 2:
            raise ValueError(
                f"FETCH_QUERY_STR_NATION_CANDIDATE entry {nation_pair!r} "
                "must contain exactly one comma separating English and Korean names"
            )
        english, korean = parts
        str_nation = ",".join(urllib.parse.quote(name) for name in (english, korean))
        str_natcd = urllib.parse.quote(natcd)
        nations.append(NationQuery(natcd, str_nation, str_natcd))
    return nations


def _build_url(
    base_url: str,
    query_format: str,
    start_date: date,
    end_date: date,
    str_nation: str,
    str_natcd: str,
) -> str:
    """Render the ``0601_excel.php`` export URL for one nation and date range.

    Args:
        base_url: Value of ``FETCH_BASE_URL``, prepended to the rendered query.
        query_format: Value of ``FETCH_QUERY_FORMAT``, a ``string.Template``
            pattern with ``$START_DATE``/``$END_DATE``/``$STR_NATION``/``$STR_NATCD``
            placeholders.
        start_date: First day of the export's date range.
        end_date: Last day of the export's date range.
        str_nation: URL-encoded ``str_nation`` query value (see :class:`NationQuery`).
        str_natcd: URL-encoded ``str_natcd`` query value (see :class:`NationQuery`).

    Returns:
        The full URL to download, with dates formatted as ``YYYY-MM-DD``.
    """
    query = Template(query_format).substitute(
        START_DATE=start_date.isoformat(),
        END_DATE=end_date.isoformat(),
        STR_NATION=str_nation,
        STR_NATCD=str_natcd,
    )
    return base_url + query


def _download(url: str, timeout: float = 30.0) -> bytes:
    """Download ``url`` with a browser-like User-Agent.

    Args:
        url: URL to fetch.
        timeout: Socket timeout in seconds.

    Returns:
        The raw response body.

    Raises:
        urllib.error.URLError: If the request fails or times out.
    """
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _is_past_month(month_start: date, today: date) -> bool:
    """Return whether ``month_start``'s calendar month is strictly before ``today``'s.

    Only year and month are compared; the day-of-month is ignored, so
    ``month_start`` is expected to be the first day of its month (as
    produced by :func:`_month_ranges`).

    Args:
        month_start: First day of the month being checked.
        today: The current date to compare against.

    Returns:
        ``True`` if ``month_start`` falls in a month before ``today``'s.
    """
    return (month_start.year, month_start.month) < (today.year, today.month)


def fetch() -> list[Path]:
    """Download (or reuse) one export per nation per month, into ``DATA_DIR``.

    Reads ``FETCH_BASE_URL`` and ``FETCH_QUERY_FORMAT`` from the environment
    (see module docstring for the ``.env`` fallback), then iterates every
    nation from :func:`_nations` across every month from :func:`_month_ranges`.
    For a month strictly before the current one, an already-saved file at
    the expected path is reused as-is and not re-downloaded; otherwise the
    export is downloaded and (over)written. A download that raises
    :class:`urllib.error.URLError` is logged to stdout and skipped rather
    than failing the whole run.

    Returns:
        Every output path considered "current" after this run, one per
        nation per month, whether freshly downloaded or reused. Paths for
        months that failed to download are omitted.
    """
    _load_env_file(ENV_FILE)
    base_url = os.environ["FETCH_BASE_URL"]
    query_format = os.environ["FETCH_QUERY_FORMAT"]

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().astimezone().date()

    saved_files: list[Path] = []
    for natcd, str_nation, str_natcd in _nations():
        for start_date, end_date in _month_ranges():
            out_path = (
                DATA_DIR / f"{start_date.year}-{start_date.month:02d}_{natcd}.xls"
            )
            if out_path.exists() and _is_past_month(start_date, today):
                saved_files.append(out_path)
                continue

            url = _build_url(
                base_url, query_format, start_date, end_date, str_nation, str_natcd
            )
            try:
                data = _download(url)
            except urllib.error.URLError as exc:
                print(f"failed to download {url}: {exc}")
                continue

            out_path.write_bytes(data)
            saved_files.append(out_path)

    return saved_files


if __name__ == "__main__":
    for path in fetch():
        print(f"saved {path}")
