"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

from mlclient.xquery import cts


def run():
    return cts.element_geospatial_query(
        "origin",
        cts.point(float("nan"), 0),
    ).serialize()
