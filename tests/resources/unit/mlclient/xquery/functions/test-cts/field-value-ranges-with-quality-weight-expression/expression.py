from mlclient.xquery import cts, fn


def run():
    return cts.field_value_ranges(
        "field-names", quality_weight=fn.count(cts.search().pos(1)),
    ).compile()
