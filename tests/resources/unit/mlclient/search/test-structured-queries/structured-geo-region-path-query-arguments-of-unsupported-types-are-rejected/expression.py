from mlclient.search.structured import GeoRegionPathQuery, Point


def run():
    return GeoRegionPathQuery("/region", Point(10, 20))
