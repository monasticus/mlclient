from mlclient.functions.xqy import cts, fn


def run():
    return cts.geospatial_json_property_reference(
        "price", options=fn.string(cts.search().index(1)),
    ).compile()
