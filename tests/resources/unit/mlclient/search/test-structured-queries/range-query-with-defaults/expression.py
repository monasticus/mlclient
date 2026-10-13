from mlclient.search.structured import Element, RangeQuery


def run():
    return RangeQuery(Element("price"), 0)
