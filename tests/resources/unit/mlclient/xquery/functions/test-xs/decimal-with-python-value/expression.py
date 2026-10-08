from decimal import Decimal
from mlclient.xquery import xs


def run():
    return xs.decimal(Decimal("1.25")).compile()
