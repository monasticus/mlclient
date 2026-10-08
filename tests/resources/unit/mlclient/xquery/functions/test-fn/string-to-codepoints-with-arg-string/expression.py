from mlclient.xquery import fn


def run():
    return fn.string_to_codepoints("arg").compile()
