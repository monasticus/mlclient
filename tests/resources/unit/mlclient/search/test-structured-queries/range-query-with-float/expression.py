from mlclient.search.structured import Element, RangeQuery


def run():
    return RangeQuery(Element("price"), 2.5, index_type="xs:double")
