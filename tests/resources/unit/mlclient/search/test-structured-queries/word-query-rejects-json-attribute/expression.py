"""Test WordQuery through the public structured-query API."""

from mlclient.search.structured import Attribute, JsonProperty, WordQuery


def run():
    return WordQuery(JsonProperty("title"), "blue", attribute=Attribute("name"))
