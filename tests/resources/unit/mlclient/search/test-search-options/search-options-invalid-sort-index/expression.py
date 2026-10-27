"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import SearchOptions, SortOrder


def run():
    return SearchOptions(SortOrder("price"))
