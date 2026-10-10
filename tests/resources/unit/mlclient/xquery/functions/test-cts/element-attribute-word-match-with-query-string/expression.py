from mlclient.xquery import cts


def run():
    return cts.element_attribute_word_match(
        "item", "id", "prod*", query="needle",
    ).compile()
