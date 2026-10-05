from mlclient.functions.xqy import cts


def run():
    return cts.geospatial_region_path_reference("/p:item", units="miles").compile()
