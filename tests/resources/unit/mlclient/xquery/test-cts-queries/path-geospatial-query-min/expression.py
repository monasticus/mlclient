"""Native ``cts:path-geospatial-query`` serialization through the public CTS builder."""

from mlclient.xquery import cts


def run():
    return cts.path_geospatial_query("/item/origin", cts.point(10, 20))
