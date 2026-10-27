from mlclient.search import options as o
from mlclient.search import structured as s


def run():
    return o.SearchOptions(
        o.GeoConstraint(
            "location",
            o.GeoElementPair(
                s.Element("location"),
                s.Element("latitude"),
                s.Element("longitude"),
            ),
            annotation="Locations",
        ),
    )
