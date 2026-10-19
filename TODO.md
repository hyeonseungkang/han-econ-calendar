# TODO

## One-time setup for GitHub Actions crawl + Pages deploy

- [ ] Repo Settings → Secrets and variables → Actions → **Variables** (not Secrets — values aren't sensitive): add
  - `FETCH_BASE_URL`
  - `FETCH_QUERY_FORMAT`
  - `FETCH_QUERY_STR_NATION_CANDIDATE`
  - `FETCH_QUERY_STR_NATCD_CANDIDATE`

  Values match `.example.env` in [README.md](README.md).
- [ ] Repo Settings → Pages → Source: set to **GitHub Actions** (not a branch).
