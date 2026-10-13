from mlclient.xquery import cts


def run():
    return cts.json_property_word_match("price", "prod*", options=["checked"]).compile()
