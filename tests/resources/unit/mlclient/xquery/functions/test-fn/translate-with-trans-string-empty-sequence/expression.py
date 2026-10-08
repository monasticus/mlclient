from mlclient.xquery import fn


def run():
    return fn.translate("src", "abc", None).compile()
