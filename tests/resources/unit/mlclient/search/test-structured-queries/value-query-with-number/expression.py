from mlclient.search.structured import JsonProperty
from mlclient.search.structured import ValueQuery


def run():
    return ValueQuery(JsonProperty("count"), 7, node_type="number")
