from mlclient.xquery import cts


def run():
    return cts.field_words(
        "field-names",
        start="a",
        options="checked",
        query="needle",
        quality_weight=2.5,
        forest_ids=123,
    ).compile()
