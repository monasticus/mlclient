from mlclient.xquery import cts


def run():
    return cts.field_value_query(
        "description", "MarkLogic search", options="checked", weight=2.5,
    ).compile()
