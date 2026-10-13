from mlclient.xquery import fn


def run():
    return fn.key("product", "42", top=object())
