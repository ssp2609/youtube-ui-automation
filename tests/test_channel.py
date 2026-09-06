from config.test_data import (
    CHANNEL_NAME,
    SEARCH_SUGGESTION,
)
from pages.channel_page import ChannelPage
from pages.search_results_page import SearchResultsPage
from pages.video_page import VideoPage
from pages.youtube_home_page import YouTubeHomePage


def test_open_programming_with_mosh_channel(
    page,
):
    """
    TC03

    Open a Programming with Mosh
    video and navigate to its channel.
    """

    home_page = YouTubeHomePage(page)
    search_results_page = SearchResultsPage(page)
    video_page = VideoPage(page)
    channel_page = ChannelPage(page)

    # Search.
    home_page.open()

    home_page.verify_home_page()

    home_page.search_directly(
        SEARCH_SUGGESTION
    )

    search_results_page.verify_loaded()

    # Find first Mosh video.
    selected_video = search_results_page.find_first_video_by_channel(
        CHANNEL_NAME
    )

    # Open video.
    search_results_page.open_video(
        selected_video
    )

    video_page.verify_loaded()

    # Make sure correct channel is
    # displayed on the video page.
    actual_channel = video_page.get_channel_name()

    assert actual_channel == CHANNEL_NAME, (
        f"Expected channel: "
        f"{CHANNEL_NAME}\n"
        f"Actual channel: "
        f"{actual_channel}"
    )

    # Click channel.
    video_page.open_channel()

    # Verify correct channel page.
    channel_page.verify_channel_page_loaded()

    channel_page.verify_channel_header(
        CHANNEL_NAME
    )
