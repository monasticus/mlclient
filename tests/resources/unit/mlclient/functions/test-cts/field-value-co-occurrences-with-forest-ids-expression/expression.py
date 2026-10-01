from mlclient.functions.xqy import cts, fn


def run():
    return cts.field_value_co_occurrences(
        "field-name-1", "field-name-2", forest_ids=fn.count(cts.search().index(1)),
    ).compile()
