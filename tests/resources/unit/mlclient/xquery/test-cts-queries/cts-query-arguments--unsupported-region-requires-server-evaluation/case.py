"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

import pytest
from mlclient.xquery import cts


def run():
    query = cts.element_geospatial_query(
        "origin",
        cts.linestring([cts.point(0, 0), cts.point(1, 1)]),
    )
    with pytest.raises(TypeError) as error:
        query.serialize()
    assert str(error.value) == (
        "cts:element-geospatial-query: region: CTS region argume"
        "nt requires server evaluation, got cts:linestring([Poin"
        "t(latitude_or_wkt=0, longitude=0), Point(latitude_or_wk"
        "t=1, longitude=1)])."
    )
