## Summary

<!-- What changed and why, in a sentence or two. -->

## Checklist

- [ ] Title follows Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, ...); it becomes the
      squash-merge commit.
- [ ] `zola build` and `zola check --skip-external-links` pass, and so does the smoke suite
      (`tools/check-site`).
- [ ] Checked in dark and light at 390px, 860px and 1280px.
- [ ] Every URL in `tools/check-site/urls.txt` still resolves; new pages are added to it.
- [ ] Share images and icons regenerated if their scripts or inputs changed (`tools/og-card`, `tools/icon`).
