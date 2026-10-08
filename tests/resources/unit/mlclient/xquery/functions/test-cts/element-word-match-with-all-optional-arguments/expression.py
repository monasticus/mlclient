from mlclient.xquery import cts


def run():
    return cts.element_word_match(
        "item",
        "prod*",
        options="checked",
        query="needle",
        quality_weight=2.5,
        forest_ids=123,
    ).compile()
