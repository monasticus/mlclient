from mlclient.xquery import cts


def run():
    return cts.parse("needle", bindings=set())
