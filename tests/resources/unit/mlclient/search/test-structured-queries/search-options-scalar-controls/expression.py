"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import SearchOptions


def run():
    return SearchOptions().control("return-facets", False).control("page-length", 20)
