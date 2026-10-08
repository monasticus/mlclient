from mlclient.xquery import fn


def run():
    return fn.min("arg", collation="http://marklogic.com/collation/codepoint").compile()
