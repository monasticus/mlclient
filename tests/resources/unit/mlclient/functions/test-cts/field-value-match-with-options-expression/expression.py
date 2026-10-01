from mlclient.functions.xqy import cts, fn


def run():
    return cts.field_value_match(
        "field-names", "prod*", options=fn.string(cts.search().index(1)),
    ).compile()
