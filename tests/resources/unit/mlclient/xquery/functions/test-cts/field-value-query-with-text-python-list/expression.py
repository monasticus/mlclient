from mlclient.xquery import cts


def run():
    return cts.field_value_query(
        "description", ["MarkLogic search", 123, 2.5, True],
    ).compile()
