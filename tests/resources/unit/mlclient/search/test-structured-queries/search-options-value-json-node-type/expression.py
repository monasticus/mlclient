from mlclient.search.options import SearchOptions
from mlclient.search.structured import JsonProperty


def run():
    return SearchOptions().value_constraint(
        "price",
        JsonProperty("price"),
        node_type="number",
    )
