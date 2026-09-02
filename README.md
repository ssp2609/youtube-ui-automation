# YouTube UI Automation

End-to-end UI automation for selected YouTube journeys using Python, pytest,
Playwright and the Page Object Model.

## Test coverage

| Test | Scenario | Primary validation |
|---|---|---|
| TC01 | Search through autocomplete | Relevant search results are displayed |
| TC02 | Open and play a Programming with Mosh video | Cross-page title/channel, ad handling and playback continuity |
| TC03 | Navigate from a video to its channel | The correct channel page and header open |
| TC04 | Return from Shorts through the YouTube logo | Shorts state and final Home state |
| TC05 | Search for an invalid value | YouTube displays its no-results state |

The tests exercise navigation, element interaction, data capture,
cross-page validation, negative testing and reusable Page Objects.

## Project structure

```text
youtube-ui-automation/
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

Run the complete suite with the two workers configured in `pytest.ini`:

```powershell
pytest
```

Run sequentially for troubleshooting:

```powershell
pytest -n 0
```

Run one test module:

```powershell
pytest .\tests\test_video.py -n 0
```

Run without slow tests:

```powershell
pytest -m "not slow"
```

## Presentation mode

Browser execution is headless and full-speed by default. Enable a visible,
slowed browser for demonstrations:

```powershell
$env:HEADED = "true"
$env:SLOW_MO = "500"
pytest -n 0
```

Clear the presentation settings afterward:

```powershell
Remove-Item Env:HEADED -ErrorAction SilentlyContinue
Remove-Item Env:SLOW_MO -ErrorAction SilentlyContinue
```

## Reports and diagnostics

Every run creates:

```text
reports/
|-- logs/
|   |-- test_execution_master.log
|   |-- test_execution_gw0.log
|   `-- test_execution_gw1.log
|-- test-results/
`-- test_report.html
```

The HTML report consolidates all workers. Playwright retains screenshots,
videos and traces for failures. Open the report with:

```powershell
Start-Process .\reports\test_report.html
```

Request logs include only the URL scheme, host and path. Query strings and
temporary signed parameters are intentionally excluded.

## Design notes

- Page Objects encapsulate locators, actions and reusable state validation.
- Tests retain assertions for business journeys and cross-page data.
- URL patterns are anchored to avoid false-positive navigation checks.
- Condition-based polling is used where YouTube's Trusted Types policy blocks
  Playwright string-based page predicates.
- Slow tests are marked with `@pytest.mark.slow`.
- Parallel workers write to separate log files.

## Known limitations

These tests run against the public YouTube website. Results may vary because
of regional content, consent dialogs, experiments, advertising, network
conditions and search-result ordering. Treat this suite as an external UI
smoke/regression demonstration rather than a deterministic test of a system
owned by this repository.
