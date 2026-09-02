from pages.youtube_home_page import (
    YouTubeHomePage,
)

from pages.search_results_page import (
    SearchResultsPage,
)


SEARCH_TEXT = "python for be"

SEARCH_SUGGESTION = (
    "Python for beginners"
)

EXPECTED_KEYWORDS = [
    "python",
    "beginner",
]


def test_search_python_for_beginners(
    page,
):
    """
    TC01

    Search using autocomplete and
    verify relevant results.
    """

    home_page = (
        YouTubeHomePage(page)
    )

    search_results_page = (
        SearchResultsPage(page)
    )

    # Open YouTube.
    home_page.open()

    home_page.verify_home_page()

    # Enter partial search.
    home_page.enter_search_text(
        SEARCH_TEXT
    )

    # Select autocomplete.
    home_page.select_search_suggestion(
        SEARCH_SUGGESTION
    )

    # Verify Search Results page.
    search_results_page.verify_loaded()

    # Verify relevant results.
    search_results_page.verify_relevant_results(
        EXPECTED_KEYWORDS
    )
