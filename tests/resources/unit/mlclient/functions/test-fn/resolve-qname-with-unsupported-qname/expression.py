from mlclient.functions.xqy import fn, xpath


def run():
    return fn.resolve_qname(object(), xpath("/p:item"))
