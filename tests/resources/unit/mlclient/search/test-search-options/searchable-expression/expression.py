from mlclient.search import options as o
from mlclient.search import structured as s


def run():
    return o.SearchOptions(
        o.SearchableExpression(
            s.PathIndex("/d:doc", {"d": "https://example.com/docs"}),
        ),
    )
