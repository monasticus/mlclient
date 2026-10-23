from mlclient.search import options as o
from mlclient.search import structured as s


def run():
    return o.SearchOptions(
        o.GeoConstraint(
            "location",
            o.GeoAttributePair(
                s.Element("location"),
                s.Attribute("latitude"),
                s.Attribute("longitude"),
            ),
            annotation="Locations",
        ),
    )
