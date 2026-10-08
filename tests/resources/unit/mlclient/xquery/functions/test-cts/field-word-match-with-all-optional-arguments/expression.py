from mlclient.xquery import cts


def run():
    return cts.field_word_match(
        "field-names",
        "prod*",
        options="checked",
        query="needle",
        quality_weight=2.5,
        forest_ids=123,
    ).compile()
