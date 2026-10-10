"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import SearchOptions
from mlclient.search.structured import Element


def run():
    return SearchOptions().container_constraint("place", Element("location"))
