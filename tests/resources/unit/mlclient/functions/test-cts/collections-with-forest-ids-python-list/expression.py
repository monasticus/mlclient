from mlclient.functions.xqy import cts


def run():
    return cts.collections(forest_ids=[123]).compile()
