"""Range options reuse the public structured-query targets."""

from mlclient.search.options import Range
from mlclient.search.structured import Field


def run():
    return Range(Field("category", "https://example.com/collation"))
