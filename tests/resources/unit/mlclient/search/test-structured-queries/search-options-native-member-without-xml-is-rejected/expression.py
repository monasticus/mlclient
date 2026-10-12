"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import SearchOptions


def run():
    return SearchOptions().add({"return-facets": False})
