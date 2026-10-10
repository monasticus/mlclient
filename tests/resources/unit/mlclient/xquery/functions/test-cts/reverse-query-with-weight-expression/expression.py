from mlclient.xquery import cts, fn


def run():
    return cts.reverse_query(
        cts.search().pos(1), weight=fn.count(cts.search().pos(1)),
    ).compile()
