from mlclient.search import options as o


def run():
    return o.SearchOptions(o.PropertiesConstraint("props", "Property values"))
