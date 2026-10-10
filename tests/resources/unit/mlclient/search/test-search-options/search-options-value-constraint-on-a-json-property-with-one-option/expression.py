"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import SearchOptions
from mlclient.search.structured import JsonProperty


def run():
    return SearchOptions().value_constraint(
        "label",
        JsonProperty("label"),
        options="case-sensitive",
    )
