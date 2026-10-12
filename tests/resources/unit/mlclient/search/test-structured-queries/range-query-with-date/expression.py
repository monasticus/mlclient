from datetime import date

from mlclient.search.structured import Element, RangeQuery


def run():
    return RangeQuery(Element("date"), date(2026, 1, 2))
