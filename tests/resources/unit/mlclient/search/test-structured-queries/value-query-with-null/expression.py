from mlclient.search.structured import JsonProperty
from mlclient.search.structured import ValueQuery


def run():
    return ValueQuery(JsonProperty("count"), "", node_type="null")
