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
    )
