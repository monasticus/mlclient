from mlclient.functions.xqy import fn


def run():
    return fn.resolve_uri("items/1.xml", base=object())
