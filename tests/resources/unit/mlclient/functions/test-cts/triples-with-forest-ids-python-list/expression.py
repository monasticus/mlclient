from mlclient.functions.xqy import cts


def run():
    return cts.triples(forest_ids=[123]).compile()
