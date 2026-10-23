from mlclient.search import options as o
from mlclient.search import structured as s


def run():
    return o.SearchOptions(
        o.PropertiesConstraint("props", "Property values"),
        o.ElementQueryConstraint(
            "body",
            s.Element("body", "https://example.com/docs"),
            fragment_scope="documents",
            annotation="Legacy",
        ),
    )
