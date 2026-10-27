"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import CollectionConstraint, SearchOptions


def run():
    return SearchOptions(CollectionConstraint("type", prefix="cts-", facet=True))
