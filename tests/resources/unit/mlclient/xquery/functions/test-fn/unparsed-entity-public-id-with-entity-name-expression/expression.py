from mlclient.xquery import cts, fn


def run():
    return fn.unparsed_entity_public_id(fn.string(cts.search().pos(1))).compile()
