from mlclient.functions.xqy import cts


def run():
    return cts.confidence_order(options=["checked"]).compile()
