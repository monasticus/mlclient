from mlclient.xquery import cts, fn


def run():
    return cts.field_value_match(
        "field-names", "prod*", options=fn.string(cts.search().pos(1)),
    ).compile()
