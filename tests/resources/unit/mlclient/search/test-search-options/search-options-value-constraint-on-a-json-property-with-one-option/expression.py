"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import SearchOptions, ValueConstraint
from mlclient.search.structured import JsonProperty


def run():
    return SearchOptions(
        ValueConstraint("label", JsonProperty("label"), options="case-sensitive"),
    )
