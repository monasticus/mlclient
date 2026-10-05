from mlclient.functions.xqy import fn


def run():
    return fn.translate("src", "abc", None).compile()
