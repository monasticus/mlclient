from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_word_query(
        "item", "MarkLogic search", weight=fn.count(cts.search().index(1)),
    ).compile()
