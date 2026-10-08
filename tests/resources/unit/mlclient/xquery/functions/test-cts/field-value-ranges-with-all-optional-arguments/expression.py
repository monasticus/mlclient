from mlclient.xquery import cts


def run():
    return cts.field_value_ranges(
        "field-names",
        bounds="bounds",
        options="checked",
        query="needle",
        quality_weight=2.5,
        forest_ids=123,
    ).compile()
