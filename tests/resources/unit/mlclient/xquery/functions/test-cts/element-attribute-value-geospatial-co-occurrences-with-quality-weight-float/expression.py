from mlclient.xquery import cts


def run():
    return cts.element_attribute_value_geospatial_co_occurrences(
        "item", "id", "item", quality_weight=2.5,
    ).compile()
