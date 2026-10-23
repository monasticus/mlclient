from mlclient.search import options as o
from mlclient.search import structured as s


def run():
    return o.SearchOptions(
        o.WordConstraint(
            "title",
            s.Element("title"),
            fragment_scope="properties",
            weight=0.5,
            annotation="Title",
            options="case-insensitive",
        ),
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
