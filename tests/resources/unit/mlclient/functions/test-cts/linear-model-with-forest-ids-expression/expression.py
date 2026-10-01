from mlclient.functions.xqy import cts, fn


def run():
    return cts.linear_model(
        cts.search().index(1), forest_ids=fn.count(cts.search().index(1)),
    ).compile()
