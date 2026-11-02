# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A tool to fetch the economic calendar data published by Hankyung (via `asp.zeroin.co.kr`) and turn it into per-nation iCalendar (`.ics`) files. Two stages: fetch raw `.xls` exports (`src/han_econ_calendar/fetch.py`), then convert them into `.ics` files (`src/han_econ_calendar/generate_ics.py`).

## Commands

This project uses `uv` (managed via `mise`; `.python-version` pins Python 3.14).

- Fetch raw exports: `uv run fetch` (or `uv run python -m han_econ_calendar.fetch`)
- Generate `.ics` files from fetched exports: `uv run generate_ics` (or `uv run python -m han_econ_calendar.generate_ics`)
- Add a dependency: `uv add <package>`
- Sync the environment: `uv sync`
- Format: `uv run ruff format .`
- Lint: `uv run ruff check .`

There are no tests configured in this repo yet.

## Architecture

- `src/han_econ_calendar/__init__.py` — exposes `fetch()` and `generate_ics()`, wired to the `fetch` and `generate_ics` console scripts in `pyproject.toml`.
- `src/han_econ_calendar/fetch.py` — downloads raw economic-calendar exports:
  - Reads `FETCH_BASE_URL`, `FETCH_QUERY_FORMAT`, `FETCH_QUERY_STR_NATION_CANDIDATE`, `FETCH_QUERY_STR_NATCD_CANDIDATE` from the environment, falling back to loading them from the `.env` file at the workspace root if not already set.
  - `FETCH_QUERY_FORMAT` is a `string.Template`-style query string (see `.env`) pointing at the `0601_excel.php` export endpoint on `asp.zeroin.co.kr`, with `$START_DATE`/`$END_DATE` (format `YYYY-MM-DD`), `$STR_NATION`, and `$STR_NATCD` placeholders.
  - `FETCH_QUERY_STR_NATION_CANDIDATE` and `FETCH_QUERY_STR_NATCD_CANDIDATE` are `|`-delimited, position-matched lists (english,korean name pair / natcd) describing each nation to fetch.
  - Iterates every nation, and for each nation every calendar month (Jan–Dec) across last year, this year, and next year, downloading one export per nation-month.
  - Saves each response to `<workspace_dir>/data/<year>-<month>_<natcd>.xls` (`data/` is gitignored on `main`; fetched exports are committed to the `data-storage` branch instead, periodically squashed by `.github/workflows/squash-data-branch.yml`).
- `src/han_econ_calendar/generate_ics.py` — converts fetched exports into calendars:
  - Reads every `.xls` file in `data/`, parsing `<year>-<month>_<natcd>` out of the filename (`natcd` matches `fetch.py`'s output) and grouping files by `natcd`.
  - Per file, reads columns 날짜, 시간, 국가, 경제지표, 실제, 예상, 이전, 중요도 via `pandas`/`calamine`; row dates (`MM.DD (Day)`, no year) are resolved against the file's `<year>-<month>` with a ±6-month rollover check for entries near year boundaries.
  - Builds one `vobject` iCalendar per `natcd` and writes it to `<workspace_dir>/serve/<natcd>.ics` (`serve/` is gitignored).
- `docs/datacenter.hankyung.com_economic-calendar_script.md` — a saved copy of the front-end JavaScript from the source site's calendar widget. It's reference material documenting how the upstream site's AJAX calls (`json_getData.php`, `json_getChart.php`, `0601_excel.php`) and date-range/paging logic work — not code that runs in this project. Consult it when changing how dates/params are built in `fetch.py`.
- `index.html` — currently empty; served via GitHub Pages.

## Notes

- `WORKSPACE_DIR` in `fetch.py` is derived from the file location (`parents[2]` of `fetch.py`), not the current working directory — keep that in mind if restructuring the package layout. `generate_ics.py` reuses the same `WORKSPACE_DIR`.
