"""Test GeoJsonPropertyPairQuery through its public API."""

from mlclient.search.structured import GeoJsonPropertyPairQuery, JsonProperty, Point


def run():
    return GeoJsonPropertyPairQuery(
        JsonProperty("place"),
        JsonProperty("lat"),
        JsonProperty("lon"),
        Point(10, 20),
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
