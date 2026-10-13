from mlclient.xquery import fn


def run():
    return fn.regex_group(2).compile()
