from mlclient.xquery import cts


def run():
    return cts.field_value_co_occurrences(
        "field-name-1",
        "field-name-2",
        options="checked",
        query="needle",
        quality_weight=2.5,
        forest_ids=123,
    ).compile()
