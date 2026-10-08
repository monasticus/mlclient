from mlclient.xquery import cts, fn


def run():
    return cts.field_values(
        "field-names", start=fn.count(cts.search().pos(1)),
    ).compile()
