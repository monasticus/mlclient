from mlclient.search import options as o
from mlclient.search import structured as s


def run():
    return o.SearchOptions(
        o.GeoConstraint(
            "location",
            o.GeoJsonProperty(s.JsonProperty("location"), s.JsonProperty("point")),
            annotation="Locations",
        ),
    )
