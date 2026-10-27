"""Range options reuse the public structured-query targets."""

from mlclient.search.options import Range, SearchOptions, Values
from mlclient.search.structured import Field


def run():
    return SearchOptions(
        Values("index", Range(Field("category", "https://example.com/collation"))),
    )
