from mlclient.xquery import cts, fn


def run():
    return cts.field_word_query(
        "description", "MarkLogic search", weight=fn.count(cts.search().pos(1)),
    ).compile()
