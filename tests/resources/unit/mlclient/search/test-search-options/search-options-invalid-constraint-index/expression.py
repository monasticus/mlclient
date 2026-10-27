"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import RangeConstraint, SearchOptions


def run():
    return SearchOptions(RangeConstraint("price", "price"))
