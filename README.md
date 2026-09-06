# YouTube UI Automation

End-to-end UI automation for selected YouTube journeys using Python, pytest,
Playwright and the Page Object Model.

## Test coverage

| Test | Scenario | Primary validation |
|---|---|---|
| TC01 | Search through autocomplete | Relevant search results are displayed |
| TC02 | Open and play a Programming with Mosh video | Cross-page title/channel, ad handling and playback continuity |
| TC03 | Navigate from a video to its channel | The correct channel page and header open |
| TC04 | Return from Search Results through the YouTube logo | Search Results state and final Home state |
| TC05 | Search for an invalid value | YouTube displays its no-results state |

The tests exercise navigation, element interaction, data capture,
cross-page validation, negative testing and reusable Page Objects. The suite
uses four YouTube page types: Home, Search Results, Video and Channel.

## Project structure

```text
youtube-ui-automation/
|-- config/
|   |-- __init__.py
|   |-- settings.py
|   `-- test_data.py
|-- pages/
|   |-- channel_page.py
|   |-- search_results_page.py
|   |-- video_page.py
|   `-- youtube_home_page.py
|-- tests/
|   |-- test_channel.py
|   |-- test_home_navigation.py
|   |-- test_no_results.py
|   |-- test_search.py
|   `-- test_video.py
|-- conftest.py
|-- pytest.ini
|-- requirements.txt
`-- README.md
```

## Prerequisites

- Python 3.9 or later
- Google Chrome or Playwright Chromium
- Internet access to YouTube

## Installation

PowerShell commands from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## Running tests

Run the complete suite sequentially (default):

```powershell
pytest
```

Run in parallel when explicitly required:

```powershell
pytest -n 2 --dist=load
```

Run one test module:

```powershell
pytest .\tests\test_video.py
```

Run one specific test:

```powershell
pytest .\tests\test_home_navigation.py::test_return_to_home_from_search_results
```

Run without slow tests:

```powershell
pytest -m "not slow"
```

## Presentation mode

Browser execution is headless and full-speed by default. Enable a visible,
slowed browser for demonstrations:

```powershell
$env:HEADED = "1"
$env:SLOW_MO = "500"
pytest
```

Clear the presentation settings afterward:

```powershell
Remove-Item Env:HEADED -ErrorAction SilentlyContinue
Remove-Item Env:SLOW_MO -ErrorAction SilentlyContinue
```

## Reports and diagnostics

Every sequential run creates:

```text
reports/
|-- logs/
|   `-- test_execution_master.log
|-- test-results/
`-- test_report.html
```

When xdist parallel execution is enabled, each worker writes its own log,
for example `test_execution_gw0.log` and `test_execution_gw1.log`.

The HTML report contains the complete run. When parallel execution is
explicitly enabled, worker logs remain separated. Playwright retains
screenshots, videos and traces for failures. Open the report with:

```powershell
Start-Process .\reports\test_report.html
```

Request logs include only the URL scheme, host and path. Query strings and
temporary signed parameters are intentionally excluded.

## Configuration and test data

Framework-wide values are centralized in `config/settings.py`:

- `BASE_URL`
- `DEFAULT_TIMEOUT`
- `ACTION_TIMEOUT`
- `POLL_INTERVAL_MS`

Shared scenario data is kept separately in `config/test_data.py`. Page-specific
URL patterns, locators, UI messages, scroll behaviour and playback thresholds
remain with the Page Object that owns that behaviour. This avoids turning the
configuration module into a catch-all constants file.

## Design notes

- Page Objects encapsulate locators, actions and reusable state validation.
- Tests retain assertions for business journeys and cross-page data.
- URL patterns are anchored to avoid false-positive navigation checks.
- Condition-based polling is used where YouTube's Trusted Types policy blocks
  Playwright string-based page predicates.
- Slow tests are marked with `@pytest.mark.slow`.
- Tests run sequentially by default for deterministic local/CI behaviour.
- Parallel execution remains available explicitly with `pytest -n 2 --dist=load`.
- Parallel workers write to separate log files when xdist is enabled.

## Known limitations

These tests run against the public YouTube website. Results may vary because
of regional content, consent dialogs, experiments, advertising, network
conditions and search-result ordering. Treat this suite as an external UI
smoke/regression demonstration rather than a deterministic test of a system
owned by this repository.
