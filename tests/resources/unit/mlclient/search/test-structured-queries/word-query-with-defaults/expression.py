from mlclient.search.structured import JsonProperty, WordQuery


def run():
    return WordQuery(JsonProperty("title"), "blue")
