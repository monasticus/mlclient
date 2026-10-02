from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_attribute_word_match(
        "item",
        "id",
        "prod*",
        forest_ids=[fn.count(cts.search().pos(1)), fn.count(cts.search().pos(2))],
    ).compile()
