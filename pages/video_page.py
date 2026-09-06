import logging
import re
import time

from playwright.sync_api import (
    Error as PlaywrightError,
    Page,
    expect,
)

from config.settings import (
    ACTION_TIMEOUT,
    DEFAULT_TIMEOUT,
    POLL_INTERVAL_MS,
)


LOGGER = logging.getLogger(__name__)


class VideoPage:
    SKIP_AD_CLICK_TIMEOUT = 3_000
    DEFAULT_AD_TIMEOUT_SECONDS = 60
    AD_POLL_INTERVAL_MS = 500
    PLAYBACK_PROGRESS_TIMEOUT_SECONDS = 10
    PLAYBACK_OBSERVATION_MS = 30_000
    MINIMUM_PLAYBACK_PROGRESS_SECONDS = 20

    WATCH_URL_PATTERN = re.compile(
        r"https://www\.youtube\.com/watch(?:\?.*)?$"
    )

    def __init__(self, page: Page) -> None:
        self.page = page
        self.player = page.locator("#movie_player")
        self.video = page.locator(
            "#movie_player video.html5-main-video"
        )
        self.play_button = self.player.locator(
            ".ytp-play-button"
        ).first
        self.video_title = page.locator(
            "ytd-watch-metadata h1"
        ).first

    def verify_loaded(self) -> None:
        """Verify that the Watch route and main video opened."""

        expect(self.page).to_have_url(
            self.WATCH_URL_PATTERN,
            timeout=DEFAULT_TIMEOUT,
        )
        expect(self.video).to_be_attached(timeout=DEFAULT_TIMEOUT)

    def get_title(self) -> str:
        """Return the visible video title."""

        expect(self.video_title).to_be_visible(timeout=DEFAULT_TIMEOUT)
        return self.video_title.inner_text().strip()

    def get_channel_name(self) -> str:
        """Return the channel name from watch-page metadata."""

        channel_link = self.page.locator(
            "ytd-watch-metadata ytd-channel-name a"
        ).first

        expect(channel_link).to_be_visible(timeout=DEFAULT_TIMEOUT)
        return channel_link.inner_text().strip()

    def verify_video_details(
        self,
        expected_title: str,
        expected_channel: str,
    ) -> None:
        """Verify cross-page title and channel values."""

        actual_title = self.get_title()
        actual_channel = self.get_channel_name()

        LOGGER.info(
            "Video details expected_title=%s actual_title=%s "
            "expected_channel=%s actual_channel=%s",
            expected_title,
            actual_title,
            expected_channel,
            actual_channel,
        )

        assert actual_title == expected_title, (
            f"Expected title: {expected_title}\n"
            f"Actual title: {actual_title}"
        )
        assert actual_channel == expected_channel, (
            f"Expected channel: {expected_channel}\n"
            f"Actual channel: {actual_channel}"
        )

    def is_ad_playing(self) -> bool:
        """Return True when the verified player shows an advertisement."""

        expect(self.player).to_be_attached(timeout=DEFAULT_TIMEOUT)
        return bool(
            self.player.evaluate(
                "player => player.classList.contains('ad-showing')"
            )
        )

    def skip_ad_if_available(self) -> bool:
        """Click a visible YouTube Skip Ad control when available."""

        selectors = (
            ".ytp-skip-ad-button",
            ".ytp-skip-ad-button-modern",
            ".ytp-ad-skip-button",
            ".ytp-ad-skip-button-modern",
            ".ytp-ad-skip-button-slot button",
        )

        for selector in selectors:
            buttons = self.player.locator(selector)

            for index in range(buttons.count()):
                button = buttons.nth(index)

                if not button.is_visible():
                    continue

                try:
                    button.click(timeout=self.SKIP_AD_CLICK_TIMEOUT)
                    LOGGER.info("Skip Ad clicked using %s", selector)
                    return True
                except PlaywrightError as error:
                    LOGGER.warning(
                        "Visible Skip Ad control could not be clicked: %s",
                        error,
                    )

        return False

    def handle_ad_if_present(
        self,
        timeout_seconds: int = DEFAULT_AD_TIMEOUT_SECONDS,
    ) -> None:
        """Skip an active ad or wait for it to finish."""

        if not self.is_ad_playing():
            LOGGER.info("No advertisement detected")
            return

        LOGGER.info("Advertisement detected")
        deadline = time.monotonic() + timeout_seconds

        while time.monotonic() < deadline:
            if not self.is_ad_playing():
                LOGGER.info("Advertisement finished")
                return

            self.skip_ad_if_available()
            self.page.wait_for_timeout(self.AD_POLL_INTERVAL_MS)

        raise AssertionError(
            "Advertisement did not finish within "
            f"{timeout_seconds} seconds."
        )

    def _wait_for_video_state(
        self,
        expression: str,
        description: str,
        timeout: int,
    ) -> None:
        """Poll a video state without page.wait_for_function()."""

        deadline = time.monotonic() + timeout / 1_000

        while time.monotonic() < deadline:
            if bool(self.video.evaluate(expression)):
                return

            self.page.wait_for_timeout(POLL_INTERVAL_MS)

        raise AssertionError(
            f"Timed out after {timeout} ms waiting for {description}."
        )

    def play_if_paused(self) -> None:
        """Start playback through the visible YouTube player control."""

        self._wait_for_video_state(
            "video => video.readyState >= 2",
            "the video to contain playable data",
            timeout=DEFAULT_TIMEOUT,
        )

        paused = bool(
            self.video.evaluate("video => video.paused")
        )

        if not paused:
            return

        expect(self.play_button).to_be_visible(timeout=ACTION_TIMEOUT)
        self.play_button.click()

        self._wait_for_video_state(
            "video => !video.paused",
            "the video to enter the playing state",
            timeout=ACTION_TIMEOUT,
        )

    def verify_video_is_playing(self) -> None:
        """Verify that playback progresses by at least one second."""

        self.play_if_paused()
        start_time = float(
            self.video.evaluate("video => video.currentTime")
        )

        deadline = (
            time.monotonic()
            + self.PLAYBACK_PROGRESS_TIMEOUT_SECONDS
        )

        while time.monotonic() < deadline:
            current_time = float(
                self.video.evaluate("video => video.currentTime")
            )

            if current_time >= start_time + 1:
                break

            self.page.wait_for_timeout(POLL_INTERVAL_MS)
        else:
            raise AssertionError(
                "Video playback did not advance by one second "
                f"within {self.PLAYBACK_PROGRESS_TIMEOUT_SECONDS} "
                "seconds."
            )

        end_time = float(
            self.video.evaluate("video => video.currentTime")
        )

        LOGGER.info(
            "Playback progressed from %.2fs to %.2fs",
            start_time,
            end_time,
        )

    def wait_30_seconds_and_verify_playing(self) -> None:
        """Wait 30 seconds and verify meaningful playback progress."""

        start_time = float(
            self.video.evaluate("video => video.currentTime")
        )
        self.page.wait_for_timeout(self.PLAYBACK_OBSERVATION_MS)
        end_time = float(
            self.video.evaluate("video => video.currentTime")
        )
        actual_progress = end_time - start_time

        LOGGER.info(
            "30-second playback check start=%.2fs end=%.2fs "
            "progress=%.2fs",
            start_time,
            end_time,
            actual_progress,
        )

        assert actual_progress >= self.MINIMUM_PLAYBACK_PROGRESS_SECONDS, (
            "Playback did not progress sufficiently during the "
            "30-second interval. Expected at least "
            f"{self.MINIMUM_PLAYBACK_PROGRESS_SECONDS}s; actual progress "
            f"was {actual_progress:.2f}s."
        )

    def open_channel(self) -> None:
        """Open the channel displayed in watch-page metadata."""

        channel_link = self.page.locator(
            "ytd-watch-metadata ytd-channel-name a"
        ).first

        expect(channel_link).to_be_visible(timeout=DEFAULT_TIMEOUT)
        LOGGER.info(
            "Opening channel: %s",
            channel_link.inner_text().strip(),
        )
        channel_link.click()
