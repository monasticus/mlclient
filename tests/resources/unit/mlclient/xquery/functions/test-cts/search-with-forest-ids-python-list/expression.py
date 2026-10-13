from mlclient.xquery import cts


def run():
    return cts.search(forest_ids=[123]).compile()
