from mlclient.functions.xqy import cts, fn


def run():
    return cts.field_values(
        "field-names", forest_ids=fn.count(cts.search().index(1)),
    ).compile()
