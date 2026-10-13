from mlclient.xquery import fn


def run():
    return fn.codepoints_to_string(2).compile()
