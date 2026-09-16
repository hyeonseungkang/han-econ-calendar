─── index.html:8-10 ───
[bug · critical] The <body> is completely empty with no mount element, script import, or app
container. As the entry point for a calendar application, this page cannot boot or render any UI
yet. Add an app mount element and the application bundle script.

  <body>
-     
+     <div id="app"></div>
+     <script type="module" src="/src/main.ts"></script>
  </body>


─── index.html:5-6 ───
[security · high] No Content-Security-Policy header or <meta> tag is declared. An ICS generation app
will likely render third-party/supplied event descriptions and serve downloaded calendar files,
making it important to define a strict CSP early to mitigate XSS and data-injection risks.

  <meta name="viewport" content="width=device-width, initial-scale=1.0">
+     <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' https://*.hankyung.com;">
      <title>ICS for 한경경제캘린더</title>


─── index.html:4-6 ───
[maintainability · low] Missing base, favicon, description, and Open Graph meta tags. Without these,
the entry point may have routing/resource resolution issues and poor shareability/SEO for a calendar
application.

  <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
+     <meta name="description" content="한경경제캘린더 일정을 ICS 파일로 변환 및 다운로드합니다.">
+     <link rel="icon" type="image/svg+xml" href="/favicon.svg">
      <title>ICS for 한경경제캘린더</title>


─── src/han_econ_calendar/fetch.py:83-86 ───
[bug · high] `urllib.request.urlopen` is called without a `timeout`, so a stalled or unresponsive
server can block the process indefinitely instead of failing fast or retrying.

- def _download(url: str) -> bytes:
+ def _download(url: str, timeout: float = 30.0) -> bytes:
      request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
-     with urllib.request.urlopen(request) as response:
+     with urllib.request.urlopen(request, timeout=timeout) as response:
          return response.read()


─── src/han_econ_calendar/fetch.py:96-108 ───
[bug · high] The fetch loop has no error handling for network or HTTP failures
(`urllib.error.HTTPError`, `URLError`, socket errors, etc.), so a single transient failure aborts
the entire batch after already having downloaded some files.

      saved_files = []
      for natcd, str_nation, str_natcd in _nations():
          for start_date, end_date in _month_ranges():
+             try:
-             url = _build_url(
+                 url = _build_url(
-                 base_url, query_format, start_date, end_date, str_nation, str_natcd
+                     base_url, query_format, start_date, end_date, str_nation, str_natcd
-             )
+                 )
-             data = _download(url)
+                 data = _download(url)
+             except urllib.error.URLError as exc:
+                 print(f"failed to download {url}: {exc}")
+                 continue
  
              out_path = (
                  TEMP_DIR / f"{start_date.year}-{start_date.month:02d}_{natcd}.xls"
              )
              out_path.write_bytes(data)
              saved_files.append(out_path)


─── src/han_econ_calendar/fetch.py:61-62 ───
[bug · medium] `str_nation` values are URL-encoded component-wise, but `str_natcd` is used verbatim
from the configuration. If a `natcd` value contains reserved URL characters, the rendered URL may be
malformed or change query semantics unexpectedly.

          str_nation = ",".join(urllib.parse.quote(name) for name in (english, korean))
-         nations.append((natcd, str_nation, natcd))
+         str_natcd = urllib.parse.quote(natcd)
+         nations.append((natcd, str_nation, str_natcd))


─── src/han_econ_calendar/fetch.py:59-60 ───
[maintainability · medium] A malformed `FETCH_QUERY_STR_NATION_CANDIDATE` entry (missing comma or
extra comma) will produce a confusing raw `ValueError` from tuple unpacking instead of a clear
configuration error.

      for nation_pair, natcd in zip(nation_candidates, natcd_candidates, strict=True):
-         english, korean = nation_pair.split(",")
+         parts = nation_pair.split(",")
+         if len(parts) != 2:
+             raise ValueError(
+                 f"FETCH_QUERY_STR_NATION_CANDIDATE entry {nation_pair!r} "
+                 "must contain exactly one comma separating English and Korean names"
+             )
+         english, korean = parts


─── src/han_econ_calendar/generate_ics.py:73-73 ───
[bug · medium] The module docstring specifies the event summary format as `'[$국가]$경제지표'`, but the
implementation only uses `row['경제지표']`, dropping the country prefix. This produces calendar entries
that do not match the documented/requirement spec.

-     event.add("summary").value = f"{row['경제지표']}"
+     event.add("summary").value = f"[{row['국가']}]{row['경제지표']}"


─── src/han_econ_calendar/generate_ics.py:74-76 ───
[bug · low] The description is built as one comma-separated line, but the spec calls for 중요도 on a
new line (`실제: ..., 예상: ..., 이전: ...\n중요도: ...`). This is a mismatch with the documented output
format.

      event.add(
          "description"
-     ).value = f"실제: {row['실제']}, 예상: {row['예상']}, 이전: {row['이전']}, 중요도: {row['중요도']}"
+     ).value = f"실제: {row['실제']}, 예상: {row['예상']}, 이전: {row['이전']}\n중요도: {row['중요도']}"


─── src/han_econ_calendar/generate_ics.py:55-63 ───
[bug · medium] Any `ValueError` while parsing the time string is swallowed and silently replaced
with midnight UTC. This masks malformed/unsupported time values (e.g., "09:30 AM" or garbled cells)
and mis-positions time-sensitive economic indicators on the calendar without warning.

+     time_str = str(time_value).strip()
+     if time_str:
-     try:
+         try:
-         event_time = (
+             event_time = (
-             datetime.strptime(str(time_value).strip(), "%H:%M")
+                 datetime.strptime(time_str, "%H:%M")
-             .replace(tzinfo=UTC)
+                 .replace(tzinfo=UTC)
-             .time()
+                 .time()
-         )
+             )
-     except ValueError:
+         except ValueError as exc:
+             raise ValueError(f"unrecognized time: {time_value!r}") from exc
+     else:
          event_time = datetime.min.time()
      return datetime.combine(event_date, event_time, tzinfo=UTC)


─── src/han_econ_calendar/generate_ics.py:66-76 ───
[bug · medium] `_add_event` accesses expected Excel columns (`날짜`, `시간`, `국가`, `경제지표`, etc.) by
string key without first checking they exist. If a spreadsheet is missing or renames a column, a
`KeyError` aborts generation for the entire country/ICS file. Validate the required columns after
reading the DataFrame and surface a clear, per-file error.



─── src/han_econ_calendar/generate_ics.py:101-104 ───
[maintainability · low] The re-raised `RuntimeError` does not chain the original `CalamineError`,
causing the original traceback and error details to be lost. Use `raise ... from err` to preserve
the cause.

              try:
                  df = pd.read_excel(xls_path, dtype=str, engine="calamine").fillna("")
-             except CalamineError:
-                 raise RuntimeError(f"Not parsable: {xls_path}")
+             except CalamineError as err:
+                 raise RuntimeError(f"Not parsable: {xls_path}") from err


─── src/han_econ_calendar/generate_ics.py:97-99 ───
[maintainability · low] Using `assert` for a runtime invariant is risky because assertions are
stripped under `python -O`. Although this path is currently filtered by `_files_by_natcd()`, the
invariant should either be removed as redundant or replaced with an explicit runtime check and a
meaningful error message.

              match = _FILENAME_RE.match(xls_path.stem)
-             assert match
+             if match is None:
+                 raise RuntimeError(f"Unexpected filename: {xls_path}")
              year, file_month = int(match["year"]), int(match["month"])


─── mise.toml:2-2 ───
[maintainability · medium] Pinning uv to 'latest' makes the build/runtime environment
non-reproducible. A future uv release can introduce breaking changes, behavior differences, or
regressions that cause CI failures or local environment drift without any code change in this
repository. Pin to a specific version (e.g., uv = '0.6.5') and update it deliberately via commit/PR
so the exact tool version is encoded in source control. If mise is intended to track latest
intentionally, document that decision in a comment.

- uv = "latest"
+ uv = "0.6.5"


─── pyproject.toml:6-6 ───
[bug · high] The minimum Python version is set to 3.14, which is the newest interpreter release and
may not be available in many deployment or CI environments. This unnecessarily blocks installation
on the widely-used 3.11–3.13 series and may conflict with dependency wheels that do not yet support
3.14. Lower the bound to the oldest version actually required by the code and supported by the
dependency set.

- requires-python = ">=3.14"
+ requires-python = ">=3.11"


─── pyproject.toml:9-9 ───
[bug · high] pandas 3.x is not a released/stable major version (the current stable line is 2.x), so
"pandas>=3.0.5" is unsatisfiable and will cause dependency resolution/installation to fail. Pin to a
released version range and revisit when pandas 3.x is actually published.

-     "pandas>=3.0.5",
+     "pandas>=2.2,<3",


─── pyproject.toml:4-4 ───
[documentation · low] The project description still contains the template placeholder text. It will
be published as package metadata if unchanged, making the project look unfinished and reducing
discoverability on PyPI.

- description = "Add your description here"
+ description = "Fetch and convert economic calendar data to ICS format"


─── pyproject.toml:19-21 ───
[maintainability · medium] "uv_build" is not a standard PEP 517 build backend and will not be
understood by pip, python -m build, or PyPI publication workflows unless every consumer has uv with
this exact backend installed. Prefer a standard backend (hatchling.build, flit_core.buildapi,
setuptools.build_meta, pdm-backend) or clearly document that the project can only be built with uv.

  [build-system]
- requires = ["uv_build>=0.12.13,<0.13.0"]
- build-backend = "uv_build"
+ requires = ["hatchling>=1.24"]
+ build-backend = "hatchling.build"


─── pyproject.toml:15-17 ───
[maintainability · low] The console script names "fetch" and "generate_ics" are generic and can
collide with scripts from other packages installed in the same environment. Use project-namespaced
names to avoid conflicts and make the CLI origin clear.

  [project.scripts]
- fetch = "han_econ_calendar:fetch"
- generate_ics = "han_econ_calendar:generate_ics"
+ han-econ-fetch = "han_econ_calendar:fetch"
+ han-econ-generate-ics = "han_econ_calendar:generate_ics"


─── pyproject.toml:1-5 ───
[maintainability · low] The [project] table lacks important metadata such as authors/maintainers,
license, repository URL, and classifiers. Missing license and classifiers hurt package
discoverability and can block publication on PyPI.

  [project]
  name = "han-econ-calendar"
  version = "0.1.0"
- description = "Add your description here"
+ description = "Fetch and convert economic calendar data to ICS format"
  readme = "README.md"
+ license = {text = "MIT"}
+ authors = [{name = "Your Name", email = "you@example.com"}]
+ classifiers = [
+     "Development Status :: 3 - Alpha",
+     "Programming Language :: Python :: 3",
+ ]


─── .gitignore:1-10 ───
[security · high] The .gitignore does not exclude common environment or credential files such as
`.env`, `.env.*`, `secrets.json`, or key/credential files. If these files exist in the working tree
they can be accidentally committed, leaking secrets or sensitive configuration into version control.
Add standard exclusions for environment and secret files (optionally keeping an `.env.example`
template tracked).

- .idea
- __pycache__
- .ruff_cache
- .venv
- 
- temp/*
- !temp/.gitkeep
- 
- serve/*
- !serve/.gitkeep
+ .env
+ .env.*
+ !.env.example
+ secrets.json
+ credentials/
+ *.pem
+ *.key
+ *.pfx
+ service-account*.json


─── .gitignore:1-4 ───
[maintainability · medium] The file ignores `__pycache__` and `.ruff_cache` but omits many other
common generated artifacts produced by Python tooling, such as `*.pyc`, `*.pyo`, `dist/`, `build/`,
`.pytest_cache/`, `.coverage`, and logs. Without these exclusions, generated files can be
accidentally committed, increasing repository noise, merge conflicts, and CI/review friction. Add a
standard set of Python/generated artifact exclusions.

- .idea
- __pycache__
- .ruff_cache
- .venv
+ *.pyc
+ *.pyo
+ *.pyd
+ .Python
+ build/
+ dist/
+ *.egg-info/
+ .pytest_cache/
+ .coverage
+ .coverage.*
+ htmlcov/
+ .tox/
+ .nox/
+ *.log
+ .DS_Store


─── .python-version:1-1 ───
[bug · critical] The `.python-version` file pins Python 3.14, but `uv.lock` resolves dependencies to
wheels targeting Python 3.15 (`cp315`), which are ABI-incompatible with the selected interpreter and
can force source builds or cause `uv sync`/`uv run` failures. Regenerate the lock file with Python
3.14 active, or—until the 3.14 wheel ecosystem is mature—align `pyproject.toml`, `.python-version`,
and `uv.lock` to a stable version such as 3.13.x.

- 3.14
+ 3.13.8