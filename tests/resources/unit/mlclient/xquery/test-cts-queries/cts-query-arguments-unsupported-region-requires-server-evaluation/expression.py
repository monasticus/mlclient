"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

from mlclient.xquery import cts


def run():
    query = cts.element_geospatial_query(
        "origin",
        cts.linestring([cts.point(0, 0), cts.point(1, 1)]),
    )
    return query.serialize()
