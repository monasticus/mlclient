from mlclient.functions.xqy import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.valid_document_patch_path(
        "/p:item", map=StaticExpression("map:map()"),
    ).compile()
