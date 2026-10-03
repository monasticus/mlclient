from mlclient.functions.xqy import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.parse("needle", bindings=StaticExpression("map:map()")).compile()
