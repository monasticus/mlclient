"""Test GeoJsonPropertyQuery through its public API."""

import pytest
from mlclient.search.structured import GeoJsonPropertyQuery, Point


def run():
    with pytest.raises(TypeError) as exc:
        GeoJsonPropertyQuery("location", Point(10, 20))
    assert (
        str(exc.value)
        == "Geospatial JSON property selectors must be JsonProperty instances."
    )
