from mlclient.xquery import cts, fn


def run():
    return cts.field_values(
        "field-names", options=fn.string(cts.search().pos(1)),
    ).compile()
