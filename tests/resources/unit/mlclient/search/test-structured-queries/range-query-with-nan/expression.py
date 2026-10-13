from mlclient.search.structured import Element, RangeQuery


def run():
    return RangeQuery(Element("price"), float("nan"), index_type="xs:double")
