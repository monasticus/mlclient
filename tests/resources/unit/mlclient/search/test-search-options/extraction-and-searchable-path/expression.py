from mlclient.search import options as o
from mlclient.search import structured as s


def run():
    return o.SearchOptions(
        o.ExtractDocumentData(
            ["/d:doc/d:title", "/d:doc/d:summary"],
            selected="include",
            namespaces={"d": "https://example.com/docs"},
        ),
        o.SearchableExpression(
            s.PathIndex("/d:doc", {"d": "https://example.com/docs"}),
        ),
    )
