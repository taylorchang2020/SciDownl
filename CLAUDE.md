# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

SciDownl is an unofficial Python library + CLI for downloading papers from SciHub by DOI, PMID, or TITLE. It maintains a local SQLite database of working SciHub mirror domains and picks the best one automatically when downloading. Distributed on PyPI as `scidownl`; entry point `scidownl=scidownl.api.cli:cli`.

## Commands

```bash
# Install for development (editable)
pip install -e .

# Run the CLI
scidownl download --doi 10.1016/j.xxx --out ./paper.pdf
scidownl domain.update --mode crawl    # refresh mirror list (or --mode search, slower brute force)
scidownl domain.list                   # show saved mirrors + success/failed counts
scidownl config --location             # print path of the global.ini config file

# Tests (stdlib unittest, NOT pytest config)
python -m unittest discover -s test            # run all
python -m unittest test.core.test_task         # run one module
python -m unittest test.db.test_service.TestService.test_add_urls  # run one test
```

**Tests hit the live network and SciHub mirrors.** `test/core/test_task.py` downloads real papers; results depend on whether SciHub mirrors are currently reachable, so failures are often environmental, not code bugs. The DB-layer tests (`test/db/`) use a separate `test-scidownl.db` via the `test=True` flag on `get_engine`/`ScihubUrlService`.

## Architecture

The download flow is a **pipeline of single-responsibility steps**, all coordinated by a `ScihubTask` that carries a shared `context` dict. Abstract base classes live in `scidownl/core/base.py`; each concrete step is a separate module in `scidownl/core/`.

Pipeline for one download (`ScihubTask._run` in `scidownl/core/task.py`):

1. **Source** (`source.py`) — wraps the user keyword as a `DoiSource` / `PmidSource` / `TitleSource`. Each is a `dict` keyed by its `type`. Registered in the `source_classes` map.
2. **Crawler** (`crawler.py`) — `ScihubCrawler` POSTs the source identifier to a chosen mirror, returns `HtmlContent`.
3. **Extractor** (`extractor.py`) — `HtmlPdfExtractor` parses the HTML (BeautifulSoup) to find the PDF URL (via configurable `#pdf` CSS selector) and the paper title, producing `PdfUrlTitleInformation`.
4. **Downloader** (`downloader.py`) — `UrlDownloader` fetches the PDF to the resolved output path.

**Mirror selection.** `ScihubTask.run` iterates a `ScihubUrlChooser` (`chooser.py`). Default is `AvailabilityFirstScihubUrlChooser`, which sorts mirrors by failure rate `failed/(success+failed+0.01)`. On crawl/extract failure the task logs, increments that mirror's `failed_times`, and tries the next mirror; on success it increments `success_times`. If the mirror DB is empty, it auto-runs a domain update first. A specific `--scihub-url` bypasses the chooser entirely.

**Domain updaters** (`updater.py`): `CrawlingScihubDomainUpdater` (default, scrapes a domain-source site) and `SearchScihubDomainUpdater` (brute-forces `sci-hub.XX` combinations with a thread pool). Registered in `scihub_domain_updaters`.

**Persistence** (`scidownl/db/`): single `ScihubUrl` SQLAlchemy entity (url, success_times, failed_times) in a SQLite file `scidownl.db` stored *inside the installed package dir* (`scidownl/`). All DB access goes through `ScihubUrlService`.

**API surface**: `scidownl/api/scihub.py` exposes `scihub_download(...)` (re-exported from `scidownl/__init__.py`), a thin wrapper that builds and runs a `ScihubTask`. `scidownl/api/cli.py` is the Click CLI that fans out multiple `--doi/--pmid/--title` options into one task each.

## Conventions & gotchas

- **Registry-map pattern is how new variants are wired in.** To add a source type, chooser, or updater, implement the base class and add it to the corresponding dict (`source_classes`, `scihub_url_choosers`, `scihub_domain_updaters`). The string keys are what users select via config/CLI.
- **All tunable behavior lives in `scidownl/config/global.ini`**, read through the `get_config()` singleton (`config.py`). This includes the PDF CSS selector, mirror-source URL, regex patterns, chooser type, DB name, log format, and proxy defaults. Prefer adding a config key over hardcoding when behavior might need to change as SciHub evolves — this is an explicit design goal ("encapsulate possible future changes as configuration").
- **Pipeline steps mutate `task.context`** to pass state and record `status`/`error`/`referer`. Steps double as `BaseTaskStep` (holding a `task` ref) so they can read proxies and write status. Keep this contract when adding steps.
- **Logging uses `loguru`** via `get_logger()` (`log.py`), formatted per the `[log]` config section. Use the logger, not `print` (except CLI table output in `domain.list`).
- **Custom exceptions** in `scidownl/exception.py` (`CrawlException`, `ExtractException`, `EmptyDoiException`, etc.) — raise these from pipeline steps so the task loop can catch and fall through to the next mirror.
- Python 3.5+ codebase; type hints used on signatures but no enforced formatter/linter config is committed.
```
