from mlclient.functions.xqy import xdmp


def run():
    return xdmp.exists("/p:item").compile(
        namespaces={"p": "https://monasticus.com/mlclient/examples/x"},
    )
