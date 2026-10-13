from mlclient.search.structured import JsonProperty, ValueQuery


def run():
    return ValueQuery(JsonProperty("count"), 7, node_type="number")
