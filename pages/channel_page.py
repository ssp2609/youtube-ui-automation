import logging
import re

from playwright.sync_api import Page, expect


LOGGER = logging.getLogger(__name__)


class ChannelPage:
    CHANNEL_URL_PATTERN = re.compile(
        r"https://www\.youtube\.com/"
        r"(?:@[^/?]+|channel/[^/?]+|c/[^/?]+)"
        r"(?:/[^?]*)?(?:\?.*)?$"
    )

    def __init__(self, page: Page) -> None:
        self.page = page

    def verify_channel_page_loaded(self) -> None:
        """Verify that a supported YouTube channel route opened."""

        expect(self.page).to_have_url(
            self.CHANNEL_URL_PATTERN,
            timeout=15_000,
        )

    def verify_channel_header(
        self,
        expected_channel: str,
    ) -> None:
        """Verify the expected channel heading is visible."""

        heading = self.page.get_by_role(
            "heading",
            name=re.compile(
                rf"^{re.escape(expected_channel)}"
                rf"(,\s*Verified)?$",
                re.IGNORECASE,
            ),
            level=1,
        )

        expect(heading).to_be_visible(timeout=15_000)

        LOGGER.info(
            "Correct channel page opened: %s",
            expected_channel,
        )
