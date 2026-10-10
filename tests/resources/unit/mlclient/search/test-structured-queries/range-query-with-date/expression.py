from mlclient.search.structured import Element, RangeQuery
from datetime import date


def run():
    return RangeQuery(Element("date"), date(2026, 1, 2))
