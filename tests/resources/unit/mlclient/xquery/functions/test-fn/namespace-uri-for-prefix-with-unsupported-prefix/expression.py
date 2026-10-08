from mlclient.xquery import fn, xpath


def run():
    return fn.namespace_uri_for_prefix(object(), xpath("/p:item"))
