from mlclient.xquery import fn


def run():
    return fn.escape_uri("products/Mark Logic", True).compile()
