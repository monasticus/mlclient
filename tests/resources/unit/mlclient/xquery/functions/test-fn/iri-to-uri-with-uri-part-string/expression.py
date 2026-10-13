from mlclient.xquery import fn


def run():
    return fn.iri_to_uri("products/Mark Logic").compile()
