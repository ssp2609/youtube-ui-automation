import pytest

from pages.youtube_home_page import YouTubeHomePage


SHORTS_DWELL_MS = 10_000


@pytest.mark.slow
def test_youtube_logo_returns_to_home(page) -> None:
    """
    TC04

    Home
    -> Shorts
    -> Wait 10 seconds
    -> YouTube logo
    -> Home
    """

    home_page = YouTubeHomePage(page)

    # Step 1: Open and verify Home.
    home_page.open()
    home_page.verify_home_page()

    # Step 2: Open and verify Shorts.
    home_page.open_shorts()
    home_page.verify_shorts_page_loaded()

    # Step 3: Remain on Shorts for the required 10 seconds.
    page.wait_for_timeout(SHORTS_DWELL_MS)

    # Confirm Shorts is still in the expected state.
    home_page.verify_shorts_page_loaded()

    # Step 4: Return Home using the YouTube logo.
    home_page.click_youtube_logo()

    # Step 5: Verify the final Home state.
    home_page.verify_home_page()