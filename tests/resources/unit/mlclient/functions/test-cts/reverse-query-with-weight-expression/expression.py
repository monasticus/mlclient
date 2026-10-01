from mlclient.functions.xqy import cts, fn


def run():
    return cts.reverse_query(
        cts.search().index(1), weight=fn.count(cts.search().index(1)),
    ).compile()
