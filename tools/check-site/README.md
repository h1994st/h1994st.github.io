# check-site

Install Chromium once: `uv run --with playwright playwright install chromium`
Run the suite from the repo root: `uv run --with pytest --with playwright pytest tools/check-site -q`
`urls.txt` lists every URL the Duckquill-era site served; each must still answer.
