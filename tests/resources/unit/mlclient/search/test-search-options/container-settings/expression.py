from mlclient.search import options as o
from mlclient.search import structured as s


def run():
    return o.SearchOptions(
        o.ContainerConstraint(
            "content",
            s.JsonProperty("content"),
            fragment_scope="properties",
            annotation="Body",
        ),
    )
