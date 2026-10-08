from mlclient.xquery import cts, fn


def run():
    return cts.field_value_match(
        "field-names", fn.count(cts.search().pos(1)),
    ).compile()
