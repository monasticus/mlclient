from mlclient.xquery import cts, fn


def run():
    return cts.field_value_co_occurrences(
        "field-name-1", "field-name-2", quality_weight=fn.count(cts.search().pos(1)),
    ).compile()
