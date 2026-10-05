from mlclient.functions.xqy import cts


def run():
    return cts.json_property_word_query("price", "MarkLogic search", options=set())
