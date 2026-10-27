from mlclient.search import options as o


def run():
    return o.SearchOptions(
        o.TransformResults(
            "decorate",
            ns="https://example.com/search",
            at="/search.xqy",
            parameters=[o.Control("max-matches", 3)],
        ),
    )
