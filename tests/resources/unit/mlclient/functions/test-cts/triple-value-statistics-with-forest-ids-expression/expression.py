from mlclient.functions.xqy import cts, fn


def run():
    return cts.triple_value_statistics(
        forest_ids=fn.count(cts.search().pos(1)),
    ).compile()
