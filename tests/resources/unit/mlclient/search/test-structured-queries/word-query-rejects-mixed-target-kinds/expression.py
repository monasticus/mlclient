"""Test WordQuery through the public structured-query API."""

from mlclient.search.structured import Element, JsonProperty, WordQuery


def run():
    return WordQuery([Element("title"), JsonProperty("title")], "blue")
