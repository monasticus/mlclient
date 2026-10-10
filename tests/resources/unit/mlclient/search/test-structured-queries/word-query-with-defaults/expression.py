from mlclient.search.structured import JsonProperty
from mlclient.search.structured import WordQuery


def run():
    return WordQuery(JsonProperty("title"), "blue")
