from mlclient.functions.xqy import cts


def run():
    return cts.geospatial_co_occurrences(
        "item",
        "item",
        child_1_name_1="child-1-name-1",
        child_1_name_2="child-1-name-2",
        child_2_name_1="child-2-name-1",
        child_2_name_2="child-2-name-2",
        options="checked",
        query="needle",
        quality_weight=2.5,
        forest_ids=123,
    ).compile()
