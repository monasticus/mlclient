from mlclient.functions.xqy import cts, fn


def run():
    return cts.field_value_query(
        [fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
        "MarkLogic search",
    ).compile()
