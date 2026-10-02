from mlclient.functions.xqy import cts, fn


def run():
    return cts.field_value_match(
        "field-names", "prod*", quality_weight=fn.count(cts.search().pos(1)),
    ).compile()
