from mlclient.functions.xqy import cts, fn


def run():
    return cts.field_value_co_occurrences(
        fn.string(cts.search().pos(1)), "field-name-2",
    ).compile()
