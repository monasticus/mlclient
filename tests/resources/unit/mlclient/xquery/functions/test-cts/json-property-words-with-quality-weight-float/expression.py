from mlclient.xquery import cts


def run():
    return cts.json_property_words("price", quality_weight=2.5).compile()
