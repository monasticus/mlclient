from mlclient.xquery import xdmp


def run():
    return xdmp.unquote(
        "<report/>",
        default_namespace="https://example.com/reports",
    ).compile()
