from mlclient.xquery import cts


def run():
    return cts.triples(forest_ids=[123]).compile()
