from mlclient.search.structured import Element, RangeQuery


def run():
    return RangeQuery(Element("price"), float("inf"), index_type="xs:double")
