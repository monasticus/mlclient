from mlclient.search import options as o
from mlclient.search import structured as s


def run():
    return o.SearchOptions(
        o.GeoConstraint(
            "location",
            o.GeoRegionPath(s.PathIndex("/location/region"), coord="wgs84"),
            annotation="Locations",
        ),
    )
