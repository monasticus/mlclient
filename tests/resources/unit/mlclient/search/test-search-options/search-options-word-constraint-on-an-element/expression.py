"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import SearchOptions, WordConstraint
from mlclient.search.structured import Element


def run():
    return SearchOptions(
        WordConstraint(
            "label",
            Element("label", "https://example.com/x"),
            options=["case-insensitive", "unstemmed"],
        ),
    )
