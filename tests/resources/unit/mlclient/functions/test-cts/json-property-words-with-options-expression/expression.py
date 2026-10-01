from mlclient.functions.xqy import cts, fn


def run():
    return cts.json_property_words(
        "price", options=fn.string(cts.search().index(1)),
    ).compile()
