from mlclient.functions.xqy import cts, fn


def run():
    return cts.field_word_query(
        "description", "MarkLogic search", options=fn.string(cts.search().index(1)),
    ).compile()
