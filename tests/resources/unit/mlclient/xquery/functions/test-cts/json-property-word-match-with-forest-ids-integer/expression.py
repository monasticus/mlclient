from mlclient.xquery import cts


def run():
    return cts.json_property_word_match("price", "prod*", forest_ids=123).compile()
