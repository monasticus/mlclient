from mlclient.functions.xqy import cts, fn


def run():
    return cts.field_value_query(
        "description", "MarkLogic search", weight=fn.count(cts.search().index(1)),
    ).compile()
