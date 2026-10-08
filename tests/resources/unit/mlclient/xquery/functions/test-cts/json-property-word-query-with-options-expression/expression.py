from mlclient.xquery import cts, fn


def run():
    return cts.json_property_word_query(
        "price", "MarkLogic search", options=fn.string(cts.search().pos(1)),
    ).compile()
