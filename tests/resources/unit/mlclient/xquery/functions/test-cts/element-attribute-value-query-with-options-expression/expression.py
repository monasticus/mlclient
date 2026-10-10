from mlclient.xquery import cts, fn


def run():
    return cts.element_attribute_value_query(
        "item", "id", "MarkLogic search", options=fn.string(cts.search().pos(1)),
    ).compile()
