from mlclient.xquery import cts


def run():
    return cts.json_property_words(
        "price",
        start="a",
        options="checked",
        query="needle",
        quality_weight=2.5,
        forest_ids=123,
    ).compile()
