from mlclient.xquery import xdmp


def run():
    return xdmp.unquote("<report/>", default_namespace="urn:reports").compile()
