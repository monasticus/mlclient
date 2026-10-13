from mlclient.search.structured import GeoRegionPathQuery, PathIndex, Point


def run():
    return GeoRegionPathQuery(PathIndex("/region"), Point(10, 20), operator="bogus")
