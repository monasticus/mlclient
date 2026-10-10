from mlclient.xquery import cts


def run():
    return cts.field_value_query(
        "description", "MarkLogic search", weight=2.5,
    ).compile()
