from mlclient.functions.xqy import cts


def run():
    return cts.element_words("item", quality_weight=None).compile()
