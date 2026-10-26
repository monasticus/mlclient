"""Range options reuse the public structured-query targets."""

from mlclient.search.options import Range, SearchOptions, Values
from mlclient.search.structured import JsonProperty


def run():
    return SearchOptions(Values("index", Range(JsonProperty("price"), "xs:decimal")))
