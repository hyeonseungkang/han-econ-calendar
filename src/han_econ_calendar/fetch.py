"""
get FETCH_BASE_URL, FETCH_QUERY_FORMAT, FETCH_QUERY_STR_NATION_CANDIDATE,
FETCH_QUERY_STR_NATCD_CANDIDATE from env
str_nation is english, korean two paired-comma joined str, must be one str
loop per nation: str_nation and str_natcd entries match by position
iterate month by month, jan to dec, in this year and -1y, +1y
save files in <workspace_dir>/temp/
"""

import calendar
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path
from string import Template

WORKSPACE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = WORKSPACE_DIR / ".env"
TEMP_DIR = WORKSPACE_DIR / "temp"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _month_ranges() -> list[tuple[date, date]]:
    this_year = datetime.now().astimezone().year
    return [
        (date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1]))
        for year in (this_year - 1, this_year, this_year + 1)
        for month in range(1, 13)
    ]


def _nations() -> list[tuple[str, str, str]]:
    """Each item: (natcd, str_nation query value, str_natcd query value)."""
    nation_candidates = os.environ["FETCH_QUERY_STR_NATION_CANDIDATE"].split("|")
    natcd_candidates = os.environ["FETCH_QUERY_STR_NATCD_CANDIDATE"].split("|")

    if len(nation_candidates) != len(natcd_candidates):
        raise ValueError(
            "FETCH_QUERY_STR_NATION_CANDIDATE and FETCH_QUERY_STR_NATCD_CANDIDATE "
            "must have the same number of entries"
        )

    nations = []
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
        nations.append((natcd, str_nation, str_natcd))
    return nations


def _build_url(
    base_url: str,
    query_format: str,
    start_date: date,
    end_date: date,
    str_nation: str,
    str_natcd: str,
) -> str:
    query = Template(query_format).substitute(
        START_DATE=start_date.isoformat(),
        END_DATE=end_date.isoformat(),
        STR_NATION=str_nation,
        STR_NATCD=str_natcd,
    )
    return base_url + query


def _download(url: str, timeout: float = 30.0) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def fetch() -> list[Path]:
    _load_env_file(ENV_FILE)
    base_url = os.environ["FETCH_BASE_URL"]
    query_format = os.environ["FETCH_QUERY_FORMAT"]

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    saved_files = []
    for natcd, str_nation, str_natcd in _nations():
        for start_date, end_date in _month_ranges():
            url = _build_url(
                base_url, query_format, start_date, end_date, str_nation, str_natcd
            )
            try:
                data = _download(url)
            except urllib.error.URLError as exc:
                print(f"failed to download {url}: {exc}")
                continue

            out_path = (
                TEMP_DIR / f"{start_date.year}-{start_date.month:02d}_{natcd}.xls"
            )
            out_path.write_bytes(data)
            saved_files.append(out_path)

    return saved_files


if __name__ == "__main__":
    for path in fetch():
        print(f"saved {path}")
