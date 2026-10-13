from mlclient.xquery import cts


def run():
    return cts.element_attribute_pair_geospatial_value_match(
        "item",
        "latitude",
        "longitude",
        "prod*",
        options="checked",
        query="needle",
        quality_weight=2.5,
        forest_ids=123,
    ).compile()
