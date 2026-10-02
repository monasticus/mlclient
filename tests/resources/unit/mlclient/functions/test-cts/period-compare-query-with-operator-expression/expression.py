from mlclient.functions.xqy import cts, fn


def run():
    return cts.period_compare_query(
        "system", fn.string(cts.search().pos(1)), "valid",
    ).compile()
