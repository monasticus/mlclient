"""Test GeoJsonPropertyQuery through its public API."""

from mlclient.search.structured import GeoJsonPropertyQuery, JsonProperty, Point


def run():
    return GeoJsonPropertyQuery(
        JsonProperty("location"),
        Point(10, 20),
        parent=JsonProperty("place"),
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
