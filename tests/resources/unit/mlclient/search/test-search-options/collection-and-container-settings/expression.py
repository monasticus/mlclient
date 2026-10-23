from mlclient.search import options as o
from mlclient.search import structured as s


def run():
    return o.SearchOptions(
        o.CollectionConstraint(
            "tag",
            prefix="https://example.com/tags/",
            options=["limit=3"],
            annotation="Tags",
        ),
        o.ContainerConstraint(
            "content",
            s.JsonProperty("content"),
            fragment_scope="properties",
            annotation="Body",
        ),
    )
