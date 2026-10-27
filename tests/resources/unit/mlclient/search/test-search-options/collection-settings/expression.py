from mlclient.search import options as o


def run():
    return o.SearchOptions(
        o.CollectionConstraint(
            "tag",
            prefix="https://example.com/tags/",
            options=["limit=3"],
            annotation="Tags",
        ),
    )
