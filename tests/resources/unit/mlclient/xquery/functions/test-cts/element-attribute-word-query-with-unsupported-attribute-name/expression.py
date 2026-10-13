from mlclient.xquery import cts


def run():
    return cts.element_attribute_word_query("item", set(), "MarkLogic search")
