from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_attribute_words(
        "item", "id", start=fn.string(cts.search().index(1)),
    ).compile()
