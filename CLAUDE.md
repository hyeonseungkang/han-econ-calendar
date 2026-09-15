# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A tool to fetch the economic calendar data published by Hankyung (via `asp.zeroin.co.kr`) and turn it into a usable calendar. `vobject` is a dependency, so the intended end output is an iCalendar (`.ics`) file, though that conversion step is not implemented yet — currently only the raw fetch step (`src/han_econ_calendar/fetch.py`) exists.

## Commands

This project uses `uv` (managed via `mise`; `.python-version` pins Python 3.14).

- Run the CLI entry point: `uv run han-econ-calendar`
- Run a module directly: `uv run python -m han_econ_calendar.fetch`
- Add a dependency: `uv add <package>`
- Sync the environment: `uv sync`

There are no tests, linter, or CI configured in this repo yet.

## Architecture

- `src/han_econ_calendar/__init__.py` — package entry point, exposes `main()` (wired to the `han-econ-calendar` console script in `pyproject.toml`).
- `src/han_econ_calendar/fetch.py` — downloads raw economic-calendar exports:
  - Reads `FETCH_URL_FORMAT` from the environment, falling back to loading it from the `.env` file at the workspace root if not already set.
  - `FETCH_URL_FORMAT` is a `string.Template`-style URL (see `.env`) pointing at the `0601_excel.php` export endpoint on `asp.zeroin.co.kr`, with `$START_DATE` and `$END_DATE` placeholders (format `YYYY-MM-DD`) and fixed query params selecting countries/importance levels.
  - Builds three date ranges — last year, this year, and next year, each spanning Jan 31 to Dec 31 — and downloads one export per range.
  - Saves each response to `<workspace_dir>/temp/<year>.xls` (`temp/` is gitignored).
- `docs/datacenter.hankyung.com_economic-calendar_script.md` — a saved copy of the front-end JavaScript from the source site's calendar widget. It's reference material documenting how the upstream site's AJAX calls (`json_getData.php`, `json_getChart.php`, `0601_excel.php`) and date-range/paging logic work — not code that runs in this project. Consult it when changing how dates/params are built for `FETCH_URL_FORMAT`.
- `docs/index.html` — currently empty; served via GitHub Pages (see recent commit history testing Pages redirects).

## Notes

- `WORKSPACE_DIR` in `fetch.py` is derived from the file location (`parents[2]` of `fetch.py`), not the current working directory — keep that in mind if restructuring the package layout.
