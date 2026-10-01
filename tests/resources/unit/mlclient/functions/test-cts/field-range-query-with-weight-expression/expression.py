from mlclient.functions.xqy import cts, fn


def run():
    return cts.field_range_query(
        "description", "=", "value", weight=fn.count(cts.search().index(1)),
    ).compile()
