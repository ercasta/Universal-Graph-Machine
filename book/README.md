# The Universal Graph Machine — the book

A multi-chapter, mobile-friendly tutorial that explains the Universal Graph
Machine to curious beginners. Built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/)
and published to GitHub Pages.

**Live site:** https://ercasta.github.io/Universal-Graph-Machine/

The playground pages run the *real* engine in the reader's browser via
[Pyodide](https://pyodide.org/) — the pure-Python `ugm` package is
compiled to a wheel and loaded with `micropip`. No server, no backend.

The pages drive `driver.pursue(trace=...)`, whose events are animated one per
card. That hook is an **observer**: `ugm.selftest` asserts a traced
search finds the identical plan to an untraced one, so the animation is the real
search rather than a re-enactment of it.

## Structure

```
book/
  mkdocs.yml            # site config + nav
  requirements.txt      # mkdocs-material
  docs/
    index.md            # landing page
    basic/              # Part 1 — Basic
    intermediate/       # Part 2 — how it decides
    advanced/           # Part 3 — when things go wrong
    deliberation/       # Part 4 — guidelines, methods, procedures, sensing
    deep/               # Part 5 — the internals
    playground/         # live Pyodide pages
    appendix/           # plain-language concept explainers
    javascripts/        # the playground widget (Pyodide loader)
    stylesheets/        # widget styling
    wheels/             # built ugm wheel (gitignored — CI builds it)
```

## Preview locally

From the repo root:

```bash
python -m pip install build -r book/requirements.txt

# Build the wheel the playground needs, into the docs tree:
python -m build --wheel --outdir book/docs/wheels .

# Serve with live reload:
cd book && mkdocs serve
```

Then open http://127.0.0.1:8000/. The playground's first "Run" downloads
Pyodide from a CDN (a few seconds); after that it's instant.

## Publishing

`.github/workflows/book.yml` builds the wheel, builds the site, and deploys to
GitHub Pages on every push to `main` that touches `book/`, `ugm/`, or
`pyproject.toml`.

**One-time setup:** in the GitHub repo, go to **Settings → Pages → Build and
deployment → Source** and choose **GitHub Actions**.
