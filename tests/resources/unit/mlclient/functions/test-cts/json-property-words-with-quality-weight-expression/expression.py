from mlclient.functions.xqy import cts, fn


def run():
    return cts.json_property_words(
        "price", quality_weight=fn.count(cts.search().pos(1)),
    ).compile()
