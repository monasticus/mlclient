"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import opt
from mlclient.search.structured import Element


def run():
    return opt.options(
        opt.word_constraint(
            "label",
            Element("label", "https://example.com/x"),
            options=["case-insensitive", "unstemmed"],
        ),
    )
