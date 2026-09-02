import re
import time

from playwright.sync_api import Locator, Page, expect


class YouTubeHomePage:
    URL = "https://www.youtube.com/"

    HOME_URL_PATTERN = re.compile(
        r"https://www\.youtube\.com/(?:\?.*)?$"
    )

    SHORTS_URL_PATTERN = re.compile(
        r"https://www\.youtube\.com/shorts(?:/[^?]*)?(?:\?.*)?$"
    )

    RESULTS_URL_PATTERN = re.compile(
        r"https://www\.youtube\.com/results(?:\?.*)?$"
    )

    def __init__(self, page: Page) -> None:
        self.page = page

        self.header = page.locator("ytd-masthead")

        self.navigation = page.locator(
            "ytd-guide-renderer, "
            "ytd-mini-guide-renderer"
        )

        self.search_box = self.header.get_by_role(
            "combobox",
            name="Search",
        )

        self.search_button = self.header.get_by_role(
            "button",
            name="Search",
            exact=True,
        )

        self.home_link = (
            self.navigation.get_by_role(
                "link",
                name="Home",
                exact=True,
            )
            .first
        )

        self.shorts_link = (
            self.navigation.get_by_role(
                "link",
                name="Shorts",
                exact=True,
            )
            .first
        )

        self.active_shorts_navigation = page.locator(
            "ytd-guide-entry-renderer"
            "[active]:has(a[href='/shorts']), "
            "ytd-mini-guide-entry-renderer"
            "[active]:has(a[href='/shorts'])"
        )

        self.shorts_content = page.locator(
            "ytd-reel-video-renderer, "
            "ytd-shorts"
        )

        self.youtube_logo = (
            self.header.get_by_role(
                "link",
                name="YouTube Home",
            )
            .first
        )

        self.category_bar = page.locator(
            "ytd-feed-filter-chip-bar-renderer"
        )

        self.empty_home_message = page.get_by_text(
            "Try searching to get started",
            exact=True,
        )

        self.all_category = (
            self.category_bar.get_by_text(
                "All",
                exact=True,
            )
        )

    def _expect_any_visible(
        self,
        *locators: Locator,
        timeout: int = 15_000,
        description: str,
    ) -> None:
        """
        Wait until at least one candidate locator is visible.

        This provides compatibility with Playwright versions that do
        not support Locator.filter(visible=True).
        """

        deadline = time.monotonic() + timeout / 1_000

        while time.monotonic() < deadline:
            for locator in locators:
                count = locator.count()

                for index in range(count):
                    if locator.nth(index).is_visible():
                        return

            # This is condition polling, not a fixed test delay.
            self.page.wait_for_timeout(100)

        raise AssertionError(
            f"Timed out after {timeout} ms waiting for "
            f"{description}."
        )

    def open(self) -> None:
        """Open YouTube Home."""

        self.page.goto(
            self.URL,
            wait_until="domcontentloaded",
        )

    def verify_home_page(self) -> None:
        """
        Verify that YouTube Home is loaded.

        A valid Home content state is either:

        1. The All category is visible.
        2. The empty Home message is visible.
        """

        expect(self.page).to_have_url(
            self.HOME_URL_PATTERN,
            timeout=15_000,
        )

        expect(self.search_box).to_be_visible(
            timeout=15_000
        )

        expect(self.home_link).to_be_visible(
            timeout=15_000
        )

        self._expect_any_visible(
            self.all_category,
            self.empty_home_message,
            timeout=15_000,
            description=(
                "the Home category bar "
                "or the empty Home message"
            ),
        )

    def enter_search_text(
        self,
        text: str,
    ) -> None:
        """Enter text into the search box."""

        expect(self.search_box).to_be_visible(
            timeout=15_000
        )

        self.search_box.fill(text)

        expect(self.search_box).to_have_value(
            text,
            timeout=10_000,
        )

    def select_search_suggestion(
        self,
        suggestion_text: str,
    ) -> None:
        """
        Select an autocomplete suggestion and verify navigation.

        This workflow is separate from Search-button submission.
        """

        suggestion = (
            self.page.get_by_role(
                "option",
                name=re.compile(
                    re.escape(suggestion_text),
                    re.IGNORECASE,
                ),
            )
            .first
        )

        expect(suggestion).to_be_visible(
            timeout=10_000
        )

        suggestion.click()

        expect(self.page).to_have_url(
            self.RESULTS_URL_PATTERN,
            timeout=15_000,
        )

    def click_search(self) -> None:
        """Submit the current search using the Search button."""

        expect(self.search_button).to_be_visible(
            timeout=10_000
        )

        expect(self.search_button).to_be_enabled(
            timeout=10_000
        )

        self.search_button.click()

        expect(self.page).to_have_url(
            self.RESULTS_URL_PATTERN,
            timeout=15_000,
        )

    def search_directly(
        self,
        search_text: str,
    ) -> None:
        """Enter a search term and submit it."""

        self.enter_search_text(search_text)
        self.click_search()

    def open_shorts(self) -> None:
        """Open Shorts from the side navigation."""

        expect(self.shorts_link).to_be_visible(
            timeout=15_000
        )

        self.shorts_link.click()

    def verify_shorts_page_loaded(self) -> None:
        """Verify the Shorts route and Shorts-specific UI state."""

        expect(self.page).to_have_url(
            self.SHORTS_URL_PATTERN,
            timeout=15_000,
        )

        self._expect_any_visible(
            self.active_shorts_navigation,
            self.shorts_content,
            timeout=15_000,
            description=(
                "the active Shorts navigation entry "
                "or Shorts content"
            ),
        )

    def click_youtube_logo(self) -> None:
        """Click the YouTube logo to return Home."""

        expect(self.youtube_logo).to_be_visible(
            timeout=15_000
        )

        self.youtube_logo.click()