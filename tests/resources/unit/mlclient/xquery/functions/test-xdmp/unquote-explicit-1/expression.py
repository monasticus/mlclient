from mlclient.xquery import xdmp


def run():
    return xdmp.unquote('{"label":"blue"}').compile()
