import re


def parse_view_count(text: str) -> int:
    """
    Convert YouTube-style view counts
    into integers.

    Examples:
        "48M views" -> 48_000_000
        "1.2M views" -> 1_200_000
        "850K views" -> 850_000
        "48,794,196 views" -> 48_794_196
    """

    if not text:
        return 0

    cleaned_text = (
        text.lower()
        .replace(",", "")
        .strip()
    )

    match = re.search(
        r"([\d.]+)\s*([kmb])?",
        cleaned_text,
    )

    if not match:
        return 0

    number = float(
        match.group(1)
    )

    suffix = match.group(2)

    multipliers = {
        "k": 1_000,
        "m": 1_000_000,
        "b": 1_000_000_000,
    }

    if suffix:
        number *= multipliers[suffix]

    return int(number)


def view_counts_are_consistent(
    search_views_text: str,
    video_page_views_text: str,
) -> bool:
    """
    Compare rounded search-result views
    with watch-page views.
    """

    search_count = parse_view_count(
        search_views_text
    )

    video_count = parse_view_count(
        video_page_views_text
    )

    if (
        search_count == 0
        or video_count == 0
    ):
        return False

    search_text = (
        search_views_text.lower()
    )

    if "b" in search_text:
        tolerance = 500_000_000

    elif "m" in search_text:
        tolerance = 500_000

    elif "k" in search_text:
        tolerance = 500

    else:
        tolerance = 0

    return (
        abs(
            video_count
            - search_count
        )
        <= tolerance
    )