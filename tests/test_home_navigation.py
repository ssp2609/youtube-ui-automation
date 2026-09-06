from config.test_data import (
    SEARCH_SUGGESTION,
)
from pages.search_results_page import SearchResultsPage
from pages.youtube_home_page import YouTubeHomePage


def test_return_to_home_from_search_results(
    page,
):
    """
    TC04

    Verify that clicking the YouTube logo
    from Search Results returns the user
    to YouTube Home.
    """

    home_page = YouTubeHomePage(page)
    search_results_page = SearchResultsPage(page)

    # Open and verify YouTube Home.
    home_page.open()
    home_page.verify_home_page()

    # Navigate to Search Results.
    home_page.search_directly(
        SEARCH_SUGGESTION
    )
    search_results_page.verify_loaded()
    search_results_page.verify_results_present()

    # Return Home using the global YouTube logo.
    home_page.click_youtube_logo()

    # Verify the final Home state.
    home_page.verify_home_page()
