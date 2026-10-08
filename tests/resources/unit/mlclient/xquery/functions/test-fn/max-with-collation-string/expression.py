from mlclient.xquery import fn


def run():
    return fn.max("arg", collation="http://marklogic.com/collation/codepoint").compile()
