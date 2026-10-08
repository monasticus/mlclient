from mlclient.xquery import cts, fn


def run():
    return cts.lsqt_query(
        "temporal", options=fn.string(cts.search().pos(1)),
    ).compile()
