from mlclient.xquery import cts, fn


def run():
    return cts.field_values(
        "field-names",
        forest_ids=[fn.count(cts.search().pos(1)), fn.count(cts.search().pos(2))],
    ).compile()
