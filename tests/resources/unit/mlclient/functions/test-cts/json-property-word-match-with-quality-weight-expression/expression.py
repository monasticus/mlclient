from mlclient.functions.xqy import cts, fn


def run():
    return cts.json_property_word_match(
        "price", "prod*", quality_weight=fn.count(cts.search().index(1)),
    ).compile()
