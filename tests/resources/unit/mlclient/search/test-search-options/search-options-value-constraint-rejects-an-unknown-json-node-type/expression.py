"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import SearchOptions, ValueConstraint
from mlclient.search.structured import JsonProperty


def run():
    return SearchOptions(
        ValueConstraint("price", JsonProperty("price"), node_type="int"),
    )
