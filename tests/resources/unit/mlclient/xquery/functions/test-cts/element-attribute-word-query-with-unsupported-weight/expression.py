from mlclient.xquery import cts


def run():
    return cts.element_attribute_word_query(
        "item", "id", "MarkLogic search", weight=set(),
    )
