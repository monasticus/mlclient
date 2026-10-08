from mlclient.xquery import cts, fn


def run():
    return cts.element_attribute_value_geospatial_co_occurrences(
        "item", "id", "item", quality_weight=fn.count(cts.search().pos(1)),
    ).compile()
