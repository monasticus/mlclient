from mlclient.search.structured import GeoElementQuery, Point


def run():
    return GeoElementQuery("location", Point(10, 20))
