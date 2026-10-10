from mlclient.xquery import cts, fn


def run():
    return cts.field_value_query(
        fn.string(cts.search().pos(1)), "MarkLogic search",
    ).compile()
