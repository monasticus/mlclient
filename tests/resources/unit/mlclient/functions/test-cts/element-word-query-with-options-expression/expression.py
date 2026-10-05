from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_word_query(
        "item", "MarkLogic search", options=fn.string(cts.search().pos(1)),
    ).compile()
