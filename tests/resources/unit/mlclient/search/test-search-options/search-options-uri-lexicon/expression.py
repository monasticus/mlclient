"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import SearchOptions, Values


def run():
    return SearchOptions(Values("uris", "uri"))
