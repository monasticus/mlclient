from mlclient.xquery import cts


def run():
    return cts.element_attribute_pair_geospatial_query(
        "item", "id", "id", None,
    ).compile()
