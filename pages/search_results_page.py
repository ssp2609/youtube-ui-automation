import logging
import re
import time
from typing import List, TypedDict

from playwright.sync_api import Locator, Page, expect

from config.settings import (
    ACTION_TIMEOUT,
    DEFAULT_TIMEOUT,
    POLL_INTERVAL_MS,
)


LOGGER = logging.getLogger(__name__)


class SelectedVideo(TypedDict):
    title: str
    channel: str
    result: Locator


class SearchResultsPage:
    RESULTS_TO_CHECK = 5
    MIN_RELEVANT_RESULTS = 3
    SCROLL_STEP = 2_000
    SCROLL_VERIFY_TIMEOUT_SECONDS = 5
    LOAD_MORE_TIMEOUT = 3_000
    DEFAULT_MAX_CHANNEL_SEARCH_SCROLLS = 6

    RESULTS_URL_PATTERN = re.compile(
        r"https://www\.youtube\.com/results(?:\?.*)?$"
    )

    def __init__(self, page: Page) -> None:
        self.page = page
        self.search_page = page.locator("ytd-search")
        self.video_results = page.locator("ytd-video-renderer")
        self.no_results_message = page.get_by_text(
            "No results found",
            exact=True,
        )

    def _wait_for_rendered_state(self) -> None:
        """Wait until Search Results renders content or no-results state."""

        deadline = time.monotonic() + DEFAULT_TIMEOUT / 1_000

        while time.monotonic() < deadline:
            if self.video_results.first.is_visible():
                return

            if self.no_results_message.is_visible():
                return

            self.page.wait_for_timeout(POLL_INTERVAL_MS)

        raise AssertionError(
            "Search Results page opened but did not render either "
            "video results or the explicit no-results state within "
            f"{DEFAULT_TIMEOUT} ms."
        )

    def verify_loaded(self) -> None:
        """Verify the Search Results route and rendered page state."""

        expect(self.page).to_have_url(
            self.RESULTS_URL_PATTERN,
            timeout=DEFAULT_TIMEOUT,
        )
        expect(self.search_page).to_be_visible(
            timeout=DEFAULT_TIMEOUT,
        )
        self._wait_for_rendered_state()

    def verify_results_present(self) -> None:
        """Verify that at least one actual video result is rendered."""

        expect(self.video_results.first).to_be_visible(
            timeout=DEFAULT_TIMEOUT,
        )

    def verify_relevant_results(
        self,
        expected_keywords: List[str],
    ) -> None:
        """Verify that several initial results contain every keyword."""

        if not expected_keywords:
            raise ValueError("At least one expected keyword is required.")

        expect(self.video_results.first).to_be_visible(
            timeout=DEFAULT_TIMEOUT
        )

        number_of_results = min(
            self.video_results.count(),
            self.RESULTS_TO_CHECK,
        )
        assert number_of_results >= self.MIN_RELEVANT_RESULTS, (
            "Too few search results were available for relevance validation. "
            f"Expected at least {self.MIN_RELEVANT_RESULTS}; "
            f"found {number_of_results}."
        )

        relevant_results = 0

        for index in range(number_of_results):
            text = self.video_results.nth(index).inner_text().strip()
            lower_text = text.lower()

            is_relevant = all(
                keyword.lower() in lower_text
                for keyword in expected_keywords
            )

            LOGGER.info(
                "Search result %d relevant=%s: %s",
                index + 1,
                is_relevant,
                text.replace("\n", " | "),
            )

            if is_relevant:
                relevant_results += 1

        assert relevant_results >= self.MIN_RELEVANT_RESULTS, (
            "Too few relevant search results. "
            f"Expected keywords={expected_keywords}; "
            f"expected at least {self.MIN_RELEVANT_RESULTS} of "
            f"{number_of_results}; found {relevant_results}."
        )

    def _scroll_and_verify(
        self,
        delta_y: int,
        direction: str,
    ) -> None:
        """Scroll once and verify that a result card moved."""

        if direction not in {"down", "up"}:
            raise ValueError(f"Unsupported scroll direction: {direction}")

        anchor_result = self.video_results.first
        expect(anchor_result).to_be_attached(timeout=ACTION_TIMEOUT)

        initial_box = anchor_result.bounding_box()

        if initial_box is None:
            raise AssertionError(
                "Could not determine the initial position of the "
                "first search result."
            )

        viewport = self.page.viewport_size

        if viewport is None:
            raise AssertionError("Browser viewport size is unavailable.")

        # Wheel events are dispatched at the current pointer location.
        # Keep the pointer below YouTube's fixed header and over content.
        self.page.mouse.move(
            viewport["width"] / 2,
            viewport["height"] * 0.75,
        )
        self.page.mouse.wheel(0, delta_y)

        deadline = (
            time.monotonic()
            + self.SCROLL_VERIFY_TIMEOUT_SECONDS
        )
        current_box = initial_box

        while time.monotonic() < deadline:
            observed_box = anchor_result.bounding_box()

            if observed_box is None:
                self.page.wait_for_timeout(POLL_INTERVAL_MS)
                continue

            current_box = observed_box

            moved_in_expected_direction = (
                current_box["y"] < initial_box["y"]
                if direction == "down"
                else current_box["y"] > initial_box["y"]
            )

            if moved_in_expected_direction:
                break

            self.page.wait_for_timeout(POLL_INTERVAL_MS)
        else:
            raise AssertionError(
                f"Page did not scroll {direction} from "
                f"result Y={initial_box['y']:.1f} within "
                f"{self.SCROLL_VERIFY_TIMEOUT_SECONDS} seconds."
            )

        LOGGER.info(
            "Scrolled %s from Y=%s to Y=%s",
            direction,
            initial_box["y"],
            current_box["y"],
        )

    def scroll_down_twice_and_up_twice(self) -> None:
        """Perform and verify the TC02 scrolling interaction."""

        self._scroll_and_verify(self.SCROLL_STEP, "down")
        self._scroll_and_verify(self.SCROLL_STEP, "down")
        self._scroll_and_verify(-self.SCROLL_STEP, "up")
        self._scroll_and_verify(-self.SCROLL_STEP, "up")

    def find_first_video_by_channel(
        self,
        channel_name: str,
        max_scrolls: int = DEFAULT_MAX_CHANNEL_SEARCH_SCROLLS,
    ) -> SelectedVideo:
        """Find the first visible result belonging to the channel."""

        for scroll_number in range(max_scrolls + 1):
            result_count = self.video_results.count()

            for index in range(result_count):
                result = self.video_results.nth(index)

                # A YouTube result card can expose channel metadata through
                # several DOM variants. Channel links are more stable than
                # presentation containers such as ytd-channel-name, so match
                # only anchors whose href points to a channel route.
                channel_links = result.locator(
                    'a[href^="/@"], '
                    'a[href^="/channel/"], '
                    'a[href^="/c/"], '
                    'a[href^="/user/"]'
                )

                actual_channel = None

                for channel_index in range(channel_links.count()):
                    channel_link = channel_links.nth(channel_index)

                    try:
                        if not channel_link.is_visible():
                            continue

                        candidate_text = channel_link.inner_text().strip()
                        if not candidate_text:
                            candidate_text = (
                                channel_link.get_attribute("aria-label") or ""
                            ).strip()
                    except Exception:
                        continue

                    normalized_channel = " ".join(candidate_text.split())

                    if normalized_channel.casefold() == channel_name.casefold():
                        actual_channel = normalized_channel
                        break

                if actual_channel is None:
                    continue

                title_link = result.locator("a#video-title").first

                if not title_link.is_visible():
                    continue

                title = title_link.inner_text().strip()

                LOGGER.info(
                    "Selected video title=%s channel=%s",
                    title,
                    actual_channel,
                )

                return {
                    "title": title,
                    "channel": actual_channel,
                    "result": result,
                }

            if scroll_number < max_scrolls:
                previous_count = result_count
                self.page.mouse.wheel(0, self.SCROLL_STEP)

                try:
                    expect(
                        self.video_results.nth(previous_count)
                    ).to_be_attached(timeout=self.LOAD_MORE_TIMEOUT)
                except AssertionError:
                    LOGGER.info(
                        "No new result attached after scroll %d; "
                        "checking existing results again.",
                        scroll_number + 1,
                    )

        raise AssertionError(
            f"No visible {channel_name} video was found after "
            f"{max_scrolls} scrolls."
        )

    def open_video(self, video: SelectedVideo) -> None:
        """Open the captured video result."""

        title_link = video["result"].locator("a#video-title").first

        expect(title_link).to_be_visible(timeout=ACTION_TIMEOUT)
        title_link.scroll_into_view_if_needed()
        title_link.click()

    def verify_no_results_message(self) -> None:
        """Verify YouTube's explicit no-results state."""

        expect(self.no_results_message).to_be_visible(
            timeout=DEFAULT_TIMEOUT
        )
