from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_attribute_word_query(
        "item", "id", "MarkLogic search", weight=fn.count(cts.search().pos(1)),
    ).compile()
