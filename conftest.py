import logging
import os
from pathlib import Path
from typing import Generator
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import Page


LOGGER = logging.getLogger("test_execution")

REPORTS_DIRECTORY = Path("reports")
LOGS_DIRECTORY = REPORTS_DIRECTORY / "logs"
RESULTS_DIRECTORY = REPORTS_DIRECTORY / "test-results"


def _get_worker_id(config: pytest.Config) -> str:
    """Return the xdist worker ID or master."""

    worker_information = getattr(
        config,
        "workerinput",
        None,
    )

    if worker_information is None:
        return "master"

    return worker_information.get(
        "workerid",
        "worker",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Create reports and attach a process-safe log file."""

    LOGS_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    RESULTS_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    worker_id = _get_worker_id(config)
    log_path = LOGS_DIRECTORY / f"test_execution_{worker_id}.log"

    file_handler = logging.FileHandler(
        log_path,
        mode="w",
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | "
            "%(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    logging.getLogger().addHandler(file_handler)
    config._execution_log_handler = file_handler


def pytest_unconfigure(config: pytest.Config) -> None:
    """Close the process-specific execution log cleanly."""

    file_handler = getattr(
        config,
        "_execution_log_handler",
        None,
    )

    if file_handler is None:
        return

    logging.getLogger().removeHandler(file_handler)
    file_handler.close()


def pytest_sessionstart(session: pytest.Session) -> None:
    """Give each parallel worker a separate log file."""

    worker_id = _get_worker_id(session.config)

    log_path = (
        LOGS_DIRECTORY
        / f"test_execution_{worker_id}.log"
    )

    LOGGER.info("=" * 80)
    LOGGER.info("TEST SESSION STARTED")
    LOGGER.info("Worker: %s", worker_id)
    LOGGER.info(
        "Root directory: %s",
        session.config.rootpath,
    )
    LOGGER.info(
        "Log file: %s",
        log_path,
    )
    LOGGER.info("=" * 80)


def pytest_sessionfinish(
    session: pytest.Session,
    exitstatus: int,
) -> None:
    """Record the completion of each session."""

    worker_id = _get_worker_id(session.config)

    LOGGER.info("=" * 80)
    LOGGER.info("TEST SESSION FINISHED")
    LOGGER.info("Worker: %s", worker_id)
    LOGGER.info("Exit status: %s", exitstatus)
    LOGGER.info("=" * 80)


def pytest_runtest_logstart(
    nodeid: str,
    location: tuple,
) -> None:
    """Record the beginning of every test."""

    LOGGER.info("-" * 80)
    LOGGER.info("TEST STARTED: %s", nodeid)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item,
    call: pytest.CallInfo,
):
    """Record the result of every test phase."""

    outcome = yield
    report = outcome.get_result()

    if report.failed:
        LOGGER.error(
            "TEST FAILED | %s | Phase: %s | Duration: %.2fs",
            report.nodeid,
            report.when,
            report.duration,
        )

        LOGGER.error(
            "Failure details:\n%s",
            report.longrepr,
        )

        return

    if report.skipped:
        LOGGER.warning(
            "TEST SKIPPED | %s | Phase: %s | Reason: %s",
            report.nodeid,
            report.when,
            report.longrepr,
        )

        return

    if report.when == "call" and report.passed:
        LOGGER.info(
            "TEST PASSED | %s | Duration: %.2fs",
            report.nodeid,
            report.duration,
        )


def pytest_runtest_logfinish(
    nodeid: str,
    location: tuple,
) -> None:
    """Record the completion of every test."""

    LOGGER.info("TEST FINISHED: %s", nodeid)
    LOGGER.info("-" * 80)


def _log_browser_console(message) -> None:
    """Capture browser console messages."""

    message_type = message.type.lower()

    if message_type == "error":
        log_level = logging.ERROR
    elif message_type == "warning":
        log_level = logging.WARNING
    else:
        log_level = logging.INFO

    LOGGER.log(
        log_level,
        "BROWSER CONSOLE | %s | %s",
        message_type.upper(),
        message.text,
    )


def _log_page_error(error) -> None:
    """Capture uncaught JavaScript errors."""

    LOGGER.error(
        "PAGE ERROR | %s",
        error,
    )


def _log_failed_request(failed_request) -> None:
    """Capture failed browser requests."""

    parts = urlsplit(failed_request.url)
    sanitized_url = (
        f"{parts.scheme}://{parts.netloc}{parts.path}"
    )
    failure = failed_request.failure or "Unknown failure"
    log_level = (
        logging.INFO
        if "ERR_ABORTED" in failure
        else logging.ERROR
    )

    LOGGER.log(
        log_level,
        "REQUEST FAILED | %s | %s | %s",
        failed_request.method,
        sanitized_url,
        failure,
    )


@pytest.fixture(scope="session")
def browser_type_launch_args(
    browser_type_launch_args: dict,
) -> dict:
    """Configure the browser centrally for all tests."""

    headed = os.getenv(
        "HEADED",
        "false",
    ).lower() == "true"

    slow_mo = int(
        os.getenv(
            "SLOW_MO",
            "0",
        )
    )

    return {
        **browser_type_launch_args,
        "headless": not headed,
        "slow_mo": slow_mo,
    }


@pytest.fixture(autouse=True)
def capture_playwright_events(
    request: pytest.FixtureRequest,
) -> Generator[None, None, None]:
    """
    Capture browser events for every test using the page fixture.

    Non-Playwright tests are unaffected.
    """

    if "page" not in request.fixturenames:
        yield
        return

    page: Page = request.getfixturevalue("page")

    page.on(
        "console",
        _log_browser_console,
    )

    page.on(
        "pageerror",
        _log_page_error,
    )

    page.on(
        "requestfailed",
        _log_failed_request,
    )

    LOGGER.info(
        "Browser page created for: %s",
        request.node.nodeid,
    )

    yield

    if not page.is_closed():
        LOGGER.info(
            "Final browser URL: %s",
            page.url,
        )
