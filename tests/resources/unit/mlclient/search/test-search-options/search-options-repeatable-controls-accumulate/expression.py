"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import Control, SearchOptions


def run():
    return SearchOptions(
        Control("search-option", "unfiltered"),
        Control("search-option", "score-simple"),
    )
