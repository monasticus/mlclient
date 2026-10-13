from mlclient.search.structured import JsonProperty, ValueQuery


def run():
    return ValueQuery(JsonProperty("count"), "", node_type="null")
