import pytest

from config.test_data import (
    CHANNEL_NAME,
    SEARCH_SUGGESTION,
)
from pages.search_results_page import SearchResultsPage
from pages.video_page import VideoPage
from pages.youtube_home_page import YouTubeHomePage


@pytest.mark.slow
def test_mosh_video_playback(
    page,
):
    """
    TC02

    Scroll results, capture the first
    Programming with Mosh video,
    open it and verify playback.
    """

    home_page = YouTubeHomePage(page)
    search_results_page = SearchResultsPage(page)
    video_page = VideoPage(page)

    # Search.
    home_page.open()

    home_page.verify_home_page()

    home_page.search_directly(
        SEARCH_SUGGESTION
    )

    search_results_page.verify_loaded()

    # Scroll down twice,
    # then up twice.
    search_results_page.scroll_down_twice_and_up_twice()

    # Capture first Mosh video.
    selected_video = search_results_page.find_first_video_by_channel(
        CHANNEL_NAME
    )

    expected_title = selected_video["title"]
    expected_channel = selected_video["channel"]

    # Open captured video.
    search_results_page.open_video(
        selected_video
    )

    video_page.verify_loaded()

    # Verify same video/channel.
    video_page.verify_video_details(
        expected_title,
        expected_channel,
    )

    # Detect/skip ad.
    video_page.handle_ad_if_present()

    # Verify video starts playing.
    video_page.verify_video_is_playing()

    # Wait 30 seconds and make sure
    # playback continues.
    video_page.wait_30_seconds_and_verify_playing()
