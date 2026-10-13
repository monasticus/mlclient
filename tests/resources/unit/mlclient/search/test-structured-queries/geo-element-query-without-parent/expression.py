from mlclient.search.structured import Element, GeoElementQuery, Point


def run():
    return GeoElementQuery(Element("location"), Point(10, 20))
