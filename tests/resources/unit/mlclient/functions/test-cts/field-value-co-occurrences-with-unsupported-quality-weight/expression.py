from mlclient.functions.xqy import cts


def run():
    return cts.field_value_co_occurrences(
        "field-name-1", "field-name-2", quality_weight=set(),
    )
