"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import SearchOptions


def run():
    return (
        SearchOptions()
        .control("search-option", "unfiltered")
        .control("search-option", "score-simple")
    )
