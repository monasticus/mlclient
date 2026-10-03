from mlclient.functions.xqy import fn


def run():
    return fn.format_date(fn.current_date(), "[Y0001]-[M01]-[D01]").compile()
