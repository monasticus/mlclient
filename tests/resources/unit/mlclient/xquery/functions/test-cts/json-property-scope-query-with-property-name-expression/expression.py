from mlclient.xquery import cts, fn


def run():
    return cts.json_property_scope_query(
        fn.string(cts.search().pos(1)), "needle",
    ).compile()
