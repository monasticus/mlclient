from mlclient.functions.xqy import cts


def run():
    return cts.json_property_words("price", forest_ids=123).compile()
