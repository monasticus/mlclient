from mlclient.functions.xqy import cts


def run():
    return cts.entity_dictionary_parse("contents", options=None).compile()
