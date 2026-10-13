from mlclient.xquery import fn, xdmp


def run():
    return xdmp.unquote(
        fn.string("<report/>"),
        default_namespace="",
        options="repair-none",
    ).compile()
