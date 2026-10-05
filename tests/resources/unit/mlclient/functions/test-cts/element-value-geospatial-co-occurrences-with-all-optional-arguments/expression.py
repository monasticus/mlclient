from mlclient.functions.xqy import cts


def run():
    return cts.element_value_geospatial_co_occurrences(
        "item",
        "item",
        coord_child_name_1="coord-child-name-1",
        coord_child_name_2="coord-child-name-2",
        options="checked",
        query="needle",
        quality_weight=2.5,
        forest_ids=123,
    ).compile()
