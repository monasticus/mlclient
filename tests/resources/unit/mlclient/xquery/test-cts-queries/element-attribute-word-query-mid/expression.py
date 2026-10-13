from mlclient.xquery import cts


def run():
    return cts.element_attribute_word_query("item", "status", "ok", weight=3)
