"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import opt
from mlclient.search.structured import JsonProperty


def run():
    return opt.options(
        opt.value_constraint("price", JsonProperty("price"), node_type="int"),
    )
