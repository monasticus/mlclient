from mlclient.xquery import xdmp


def run():
    return xdmp.unquote("{}", options=["repair-none", "format-json"]).compile()
