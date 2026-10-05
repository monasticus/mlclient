from decimal import Decimal
from mlclient.functions.xqy import xs


def run():
    return xs.decimal(Decimal("Infinity"))
