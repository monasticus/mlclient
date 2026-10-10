from mlclient.xquery import fn


def run():
    return fn.analyze_string(None, "logic").compile()
