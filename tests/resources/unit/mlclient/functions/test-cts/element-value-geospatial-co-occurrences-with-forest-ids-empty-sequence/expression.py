from mlclient.functions.xqy import cts


def run():
    return cts.element_value_geospatial_co_occurrences(
        "item", "item", forest_ids=None,
    ).compile()
