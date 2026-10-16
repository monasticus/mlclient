"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import ContainerConstraint, SearchOptions
from mlclient.search.structured import Element


def run():
    return SearchOptions(ContainerConstraint("place", Element("location")))
