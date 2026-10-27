"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import NativeOptions, SearchOptions


def run():
    return SearchOptions(NativeOptions({"return-facets": False}))
