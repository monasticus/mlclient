from mlclient.search import options as o
from mlclient.xquery import cts


def run():
    return o.SearchOptions(
        o.Grammar(
            quotation='"',
            implicit=o.Implicit(cts.and_query([])),
            starters=[
                o.Starter("(", 30, "group", delimiter=")"),
                o.Starter(
                    "-",
                    40,
                    "prefix",
                    ns="https://example.com/search",
                    at="/grammar.xqy",
                    element="cts:not-query",
                    options="unfiltered",
                    tokenize="word",
                ),
            ],
            joiners=[
                o.Joiner(
                    "AND",
                    20,
                    "infix",
                    element="cts:and-query",
                    options="unordered",
                    compare="EQ",
                    consume=1,
                    tokenize="word",
                    ns="https://example.com/search",
                    at="/grammar.xqy",
                ),
            ],
        ),
    )
