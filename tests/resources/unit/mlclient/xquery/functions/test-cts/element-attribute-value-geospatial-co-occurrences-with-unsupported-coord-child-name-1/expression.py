from mlclient.xquery import cts


def run():
    return cts.element_attribute_value_geospatial_co_occurrences(
        "item", "id", "item", coord_child_name_1=set(),
    )
