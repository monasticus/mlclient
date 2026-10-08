from mlclient.xquery import cts


def run():
    return cts.element_value_query(
        "item", "MarkLogic search", options="checked", weight=2.5,
    ).compile()
