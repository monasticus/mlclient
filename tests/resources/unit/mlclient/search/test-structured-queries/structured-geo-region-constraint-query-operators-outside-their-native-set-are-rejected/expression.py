from mlclient.search.structured import GeoRegionConstraintQuery, Point


def run():
    return GeoRegionConstraintQuery("region", Point(10, 20), operator="bogus")
