from mlclient.xquery import cts, fn


def run():
    return cts.geospatial_json_property_reference(
        "price", options=fn.string(cts.search().pos(1)),
    ).compile()
