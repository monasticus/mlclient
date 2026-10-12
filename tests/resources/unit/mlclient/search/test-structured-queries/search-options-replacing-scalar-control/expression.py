"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import SearchOptions


def run():
    return SearchOptions().control("page-length", 10).control("page-length", 20)
