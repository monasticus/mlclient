from mlclient.functions.xqy import cts


def run():
    return cts.json_property_word_match("price", "prod*", options=["checked"]).compile()
