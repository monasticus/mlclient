from mlclient.search.structured import Field


def run():
    return Field("body", collation="http://marklogic.com/collation/")
