"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import Control, SearchOptions


def run():
    return SearchOptions(Control("page-length", 10), Control("page-length", 20))
