from mlclient.search.structured import GeoRegionPathQuery, PathIndex, Point


def run():
    GeoRegionPathQuery(PathIndex("/region"), Point(10, 20), operator="covered-by")
