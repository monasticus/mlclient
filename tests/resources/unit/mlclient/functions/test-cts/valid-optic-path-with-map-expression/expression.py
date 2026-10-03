from mlclient.functions.xqy import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.valid_optic_path("/p:item", map=StaticExpression("map:map()")).compile()
