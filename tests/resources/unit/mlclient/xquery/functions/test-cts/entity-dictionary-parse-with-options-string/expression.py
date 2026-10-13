from mlclient.xquery import cts


def run():
    return cts.entity_dictionary_parse("contents", options="checked").compile()
