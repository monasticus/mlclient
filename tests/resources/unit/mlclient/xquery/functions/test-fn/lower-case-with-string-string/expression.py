from mlclient.xquery import fn


def run():
    return fn.lower_case("string").compile()
