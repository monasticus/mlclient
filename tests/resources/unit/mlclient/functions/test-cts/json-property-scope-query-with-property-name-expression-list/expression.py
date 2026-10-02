from mlclient.functions.xqy import cts, fn


def run():
    return cts.json_property_scope_query(
        [fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))], "needle",
    ).compile()
