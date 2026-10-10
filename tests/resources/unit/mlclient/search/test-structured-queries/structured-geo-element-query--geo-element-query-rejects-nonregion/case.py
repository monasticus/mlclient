"""Test GeoElementQuery through its public API."""

import pytest
from mlclient.search.structured import Element, GeoElementQuery


def run():
    with pytest.raises(TypeError) as exc:
        GeoElementQuery(Element("location"), "10,20")
    assert str(exc.value) == "Geospatial criteria must be Region instances."
