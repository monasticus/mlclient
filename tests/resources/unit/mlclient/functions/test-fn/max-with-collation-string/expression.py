from mlclient.functions.xqy import fn


def run():
    return fn.max("arg", collation="http://marklogic.com/collation/codepoint").compile()
