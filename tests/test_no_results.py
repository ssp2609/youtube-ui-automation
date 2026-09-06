from config.test_data import INVALID_SEARCH
from pages.search_results_page import SearchResultsPage
from pages.youtube_home_page import YouTubeHomePage


def test_invalid_search_displays_no_results(
    page,
):
    """
    TC05

    Perform an invalid search and
    verify YouTube handles it.
    """

    home_page = YouTubeHomePage(page)
    search_results_page = SearchResultsPage(page)

    # Open YouTube.
    home_page.open()
    home_page.verify_home_page()

    # Invalid search.
    home_page.search_directly(INVALID_SEARCH)

    # Verify search page.
    search_results_page.verify_loaded()

    # Verify no-results state.
    search_results_page.verify_no_results_message()
