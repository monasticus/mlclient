from mlclient.xquery import cts, fn


def run():
    return cts.element_attribute_word_match(
        "item", "id", "prod*", forest_ids=fn.count(cts.search().pos(1)),
    ).compile()
