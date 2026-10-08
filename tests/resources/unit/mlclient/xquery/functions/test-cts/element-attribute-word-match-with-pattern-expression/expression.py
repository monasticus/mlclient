from mlclient.xquery import cts, fn


def run():
    return cts.element_attribute_word_match(
        "item", "id", fn.string(cts.search().pos(1)),
    ).compile()
