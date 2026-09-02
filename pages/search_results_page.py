import logging
import re
import time
from typing import List, TypedDict

from playwright.sync_api import Locator, Page, expect


LOGGER = logging.getLogger(__name__)


class SelectedVideo(TypedDict):
    title: str
    channel: str
    result: Locator


class SearchResultsPage:
    RESULTS_URL_PATTERN = re.compile(
        r"https://www\.youtube\.com/results(?:\?.*)?$"
    )

    def __init__(self, page: Page) -> None:
        self.page = page
        self.video_results = page.locator("ytd-video-renderer")

    def verify_loaded(self) -> None:
        """Verify that the Search Results route opened."""

        expect(self.page).to_have_url(
            self.RESULTS_URL_PATTERN,
            timeout=15_000,
        )

    def verify_relevant_results(
        self,
        expected_keywords: List[str],
    ) -> None:
        """Verify that several initial results contain every keyword."""

        if not expected_keywords:
            raise ValueError("At least one expected keyword is required.")

        expect(self.video_results.first).to_be_visible(
            timeout=15_000
        )

        number_of_results = min(self.video_results.count(), 5)
        required_relevant_results = min(3, number_of_results)
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

        assert relevant_results >= required_relevant_results, (
            "Too few relevant search results. "
            f"Expected at least {required_relevant_results} of "
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
        expect(anchor_result).to_be_attached(timeout=10_000)

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

        deadline = time.monotonic() + 5
        current_box = initial_box

        while time.monotonic() < deadline:
            observed_box = anchor_result.bounding_box()

            if observed_box is None:
                self.page.wait_for_timeout(100)
                continue

            current_box = observed_box

            moved_in_expected_direction = (
                current_box["y"] < initial_box["y"]
                if direction == "down"
                else current_box["y"] > initial_box["y"]
            )

            if moved_in_expected_direction:
                break

            self.page.wait_for_timeout(100)
        else:
            raise AssertionError(
                f"Page did not scroll {direction} from "
                f"result Y={initial_box['y']:.1f} within 5 seconds."
            )

        LOGGER.info(
            "Scrolled %s from Y=%s to Y=%s",
            direction,
            initial_box["y"],
            current_box["y"],
        )

    def scroll_down_twice_and_up_twice(self) -> None:
        """Perform and verify the TC02 scrolling interaction."""

        self._scroll_and_verify(2000, "down")
        self._scroll_and_verify(2000, "down")
        self._scroll_and_verify(-2000, "up")
        self._scroll_and_verify(-2000, "up")

    def find_first_video_by_channel(
        self,
        channel_name: str,
        max_scrolls: int = 6,
    ) -> SelectedVideo:
        """Find the first visible result belonging to the channel."""

        for scroll_number in range(max_scrolls + 1):
            result_count = self.video_results.count()

            for index in range(result_count):
                result = self.video_results.nth(index)
                result_text = result.inner_text().strip()

                if channel_name.lower() not in result_text.lower():
                    continue

                title_link = result.locator("a#video-title").first

                if not title_link.is_visible():
                    continue

                title = title_link.inner_text().strip()

                LOGGER.info(
                    "Selected video title=%s channel=%s",
                    title,
                    channel_name,
                )

                return {
                    "title": title,
                    "channel": channel_name,
                    "result": result,
                }

            if scroll_number < max_scrolls:
                previous_count = result_count
                self.page.mouse.wheel(0, 2000)

                try:
                    expect(
                        self.video_results.nth(previous_count)
                    ).to_be_attached(timeout=3_000)
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

        expect(title_link).to_be_visible(timeout=10_000)
        title_link.scroll_into_view_if_needed()
        title_link.click()

    def click_youtube_logo(self) -> None:
        """Click the YouTube logo to return Home."""

        youtube_logo = self.page.get_by_role(
            "link",
            name="YouTube Home",
        ).first

        expect(youtube_logo).to_be_visible(timeout=15_000)
        youtube_logo.click()

    def verify_no_results_message(self) -> None:
        """Verify YouTube's explicit no-results state."""

        no_results = self.page.get_by_text(
            "No results found",
            exact=True,
        )

        expect(no_results).to_be_visible(timeout=15_000)
