from mlclient.search import options as o
from mlclient.search import structured as s


def run():
    return o.SearchOptions(
        o.GeoConstraint(
            "location",
            o.GeoElement(
                s.Element("location"),
                s.Element("point"),
                options=["coordinate-system=wgs84"],
                facet_options=["limit=5"],
                fragment_scope="documents",
                weight=2,
                heatmap=o.Heatmap(-10, -20, 10, 20, 4, 8),
            ),
        ),
    )
