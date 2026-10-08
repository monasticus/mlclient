from mlclient.xquery import fn


def run():
    return fn.function_available("fn:count", arity=object())
