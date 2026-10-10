from mlclient.xquery import cts, fn


def run():
    return cts.field_range_query(
        "description", "=", fn.count(cts.search().pos(1)),
    ).compile()
