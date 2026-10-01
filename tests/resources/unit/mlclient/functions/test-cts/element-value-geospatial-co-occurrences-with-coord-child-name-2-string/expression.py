from mlclient.functions.xqy import cts


def run():
    return cts.element_value_geospatial_co_occurrences(
        "item", "item", coord_child_name_2="coord-child-name-2",
    ).compile()
