from mlclient.xquery import fn


def run():
    return fn.unparsed_entity_uri("logo").compile()
