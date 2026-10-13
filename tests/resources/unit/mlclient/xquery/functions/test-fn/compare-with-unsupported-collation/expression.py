from mlclient.xquery import fn


def run():
    return fn.compare("comparand1", "comparand2", collation=object())
