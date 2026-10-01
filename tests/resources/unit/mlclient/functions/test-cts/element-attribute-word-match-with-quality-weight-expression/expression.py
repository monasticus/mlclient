from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_attribute_word_match(
        "item", "id", "prod*", quality_weight=fn.count(cts.search().index(1)),
    ).compile()
