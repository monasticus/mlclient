from mlclient.search import options as o
from mlclient.search import structured as s


def run():
    return o.SearchOptions(
        o.ValueConstraint(
            "active",
            s.JsonProperty("active"),
            node_type="boolean",
            fragment_scope="documents",
            weight=0,
            annotation="Active",
            options=["exact"],
        ),
    )
