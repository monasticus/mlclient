from decimal import Decimal

from mlclient.search.structured import TermQuery


def run():
    return TermQuery("blue", weight=Decimal("Infinity"))
