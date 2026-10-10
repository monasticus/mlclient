"""Range options reuse the public structured-query targets."""

from mlclient.search.options import Range
from mlclient.search.structured import Element


def run():
    return Range(Element("product"), attribute="category").to_json()
