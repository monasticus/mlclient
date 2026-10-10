from mlclient.search.structured import Point
from mlclient.search.structured import Element
from mlclient.search.structured import GeoElementQuery


def run():
    return GeoElementQuery(Element("location"), Point(10, 20))
