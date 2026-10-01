from mlclient.functions.xqy import cts, fn


def run():
    return cts.lsqt_query(
        "temporal", options=fn.string(cts.search().index(1)),
    ).compile()
