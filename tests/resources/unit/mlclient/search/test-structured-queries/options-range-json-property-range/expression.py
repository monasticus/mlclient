"""Range options reuse the public structured-query targets."""

from mlclient.search.options import Range
from mlclient.search.structured import JsonProperty


def run():
    return Range(JsonProperty("price"), "xs:decimal")
