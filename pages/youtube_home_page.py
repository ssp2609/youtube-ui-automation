import re
import time

from playwright.sync_api import Locator, Page, expect

from config.settings import (
    ACTION_TIMEOUT,
    BASE_URL,
    DEFAULT_TIMEOUT,
    POLL_INTERVAL_MS,
)


class YouTubeHomePage:
    """Page Object for YouTube Home and global header interactions."""

    URL = BASE_URL

    HOME_URL_PATTERN = re.compile(
        r"https://www\.youtube\.com/(?:\?.*)?$"
    )

    RESULTS_URL_PATTERN = re.compile(
        r"https://www\.youtube\.com/results(?:\?.*)?$"
    )

    def __init__(self, page: Page) -> None:
        self.page = page

        # Global header
        self.header = page.locator("ytd-masthead")

        self.search_box = self.header.get_by_role(
            "combobox",
            name="Search",
        )

        self.search_button = self.header.get_by_role(
            "button",
            name="Search",
            exact=True,
        )

        self.youtube_logo = self.header.get_by_role(
            "link",
            name="YouTube Home",
        ).first

        # Home-specific content
        self.home_feed = page.locator(
            "ytd-rich-grid-renderer"
        )

        self.empty_home_message = page.get_by_text(
            "Try searching to get started",
            exact=True,
        )

    def _expect_any_visible(
        self,
        *locators: Locator,
        timeout: int = DEFAULT_TIMEOUT,
        description: str,
    ) -> None:
        """
        Wait until at least one supplied locator becomes visible.

        YouTube Home can show either:
        1. the normal video grid, or
        2. an empty-home state.
        """

        deadline = time.monotonic() + timeout / 1_000

        while time.monotonic() < deadline:
            for locator in locators:
                for index in range(locator.count()):
                    if locator.nth(index).is_visible():
                        return

            self.page.wait_for_timeout(POLL_INTERVAL_MS)

        raise AssertionError(
            f"Timed out after {timeout} ms waiting for "
            f"{description}."
        )

    def open(self) -> None:
        """Navigate to YouTube Home."""

        self.page.goto(
            self.URL,
            wait_until="domcontentloaded",
        )

    def verify_home_page(self) -> None:
        """
        Verify that YouTube Home is loaded.

        Primary verification:
        - Home URL

        Secondary verification:
        - Home video grid
        OR
        - valid empty-home state
        """

        expect(self.page).to_have_url(
            self.HOME_URL_PATTERN,
            timeout=DEFAULT_TIMEOUT,
        )

        self._expect_any_visible(
            self.home_feed,
            self.empty_home_message,
            timeout=DEFAULT_TIMEOUT,
            description=(
                "the YouTube Home video grid "
                "or the empty Home state"
            ),
        )

    def enter_search_text(
        self,
        text: str,
    ) -> None:
        """Enter text into the YouTube search box."""

        expect(self.search_box).to_be_visible(
            timeout=DEFAULT_TIMEOUT,
        )

        self.search_box.fill(text)

        expect(self.search_box).to_have_value(
            text,
            timeout=ACTION_TIMEOUT,
        )

    def select_search_suggestion(
        self,
        suggestion_text: str,
    ) -> None:
        """Select the expected autocomplete suggestion.

        This method is intentionally strict because autocomplete is the
        behaviour under test in TC01. If the expected suggestion is not
        rendered, the test must fail rather than silently switching to a
        different search path.
        """

        suggestion = self.page.get_by_role(
            "option",
            name=re.compile(
                re.escape(suggestion_text),
                re.IGNORECASE,
            ),
        ).first

        expect(suggestion).to_be_visible(
            timeout=ACTION_TIMEOUT,
        )
        suggestion.click()

        expect(self.page).to_have_url(
            self.RESULTS_URL_PATTERN,
            timeout=DEFAULT_TIMEOUT,
        )

    def click_search(self) -> None:
        """Submit the current search."""

        expect(self.search_button).to_be_visible(
            timeout=ACTION_TIMEOUT,
        )

        expect(self.search_button).to_be_enabled(
            timeout=ACTION_TIMEOUT,
        )

        self.search_button.click()

        expect(self.page).to_have_url(
            self.RESULTS_URL_PATTERN,
            timeout=DEFAULT_TIMEOUT,
        )

    def search_directly(
        self,
        search_text: str,
    ) -> None:
        """Enter a search term and submit it."""

        self.enter_search_text(
            search_text
        )

        self.click_search()

    def click_youtube_logo(self) -> None:
        """Click the YouTube logo to return Home."""

        expect(self.youtube_logo).to_be_visible(
            timeout=DEFAULT_TIMEOUT,
        )

        self.youtube_logo.click()

        expect(self.page).to_have_url(
            self.HOME_URL_PATTERN,
            timeout=DEFAULT_TIMEOUT,
        )
