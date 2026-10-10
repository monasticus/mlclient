"""Range options reuse the public structured-query targets."""

from mlclient.search.options import Range
from mlclient.search.structured import Attribute, JsonProperty


def run():
    return Range(JsonProperty("product"), attribute=Attribute("category")).to_xml()
