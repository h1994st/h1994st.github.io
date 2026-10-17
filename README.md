# Personal Website

Source of [shengtuo.me](https://shengtuo.me): Markdown and TOML rendered by [Zola](https://www.getzola.org/)
0.23.6, styled with [facet](https://github.com/h1994st/facet). facet is a git submodule at
`static/vendor/facet`, pinned to a release tag; only its `dist/` is published. There is no JS build step.

## Setup

```bash
git clone --recurse-submodules https://github.com/h1994st/h1994st.github.io
# or, in an existing clone:
git submodule update --init --recursive

zola serve    # dev server with live reload (add --drafts for draft pages)
zola build    # render to public/ (git-ignored)
```

## Checks

Install Chromium once: `uv run --with playwright playwright install chromium`.

```bash
# smoke suite: builds the site, then drives it in Chromium
uv run --with pytest --with playwright pytest tools/check-site -q

# share-image generator tests
uv run --with pytest --with pillow --with fonttools --with brotli pytest tools/og-card -q
```

The `Check` workflow runs both on every pull request.

## Share images and icon

```bash
# one per post, into static/cards/ (git-ignored; CI generates them before the build)
uv run --with pillow --with fonttools --with brotli tools/og-card/posts.py --out static/cards

# site-wide static/card.png
uv run --with pillow tools/og-card/render.py

# content/projects/card.png
uv run --with pillow --with resvg-py tools/og-card/projects.py

# static/favicon.svg, favicon.ico, apple-touch-icon.png
uv run --with fonttools --with brotli --with resvg-py --with pillow tools/icon/render.py
```

## Updating facet

```bash
git -C static/vendor/facet fetch --tags
git -C static/vendor/facet checkout vX.Y.Z
git add static/vendor/facet && git commit -m "chore: bump facet to vX.Y.Z"
```

## Deployment

Pushing to `master` runs `.github/workflows/build.yml`, which generates the share images, builds with
Zola and force-publishes the result to `gh-pages`. `static/CNAME` carries the custom domain.
