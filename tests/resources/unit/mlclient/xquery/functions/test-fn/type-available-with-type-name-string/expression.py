from mlclient.xquery import fn


def run():
    return fn.type_available("xs:string").compile()
