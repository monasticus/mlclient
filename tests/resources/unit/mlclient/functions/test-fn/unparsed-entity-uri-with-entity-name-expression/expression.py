from mlclient.functions.xqy import cts, fn


def run():
    return fn.unparsed_entity_uri(fn.string(cts.search().index(1))).compile()
