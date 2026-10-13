from mlclient.xquery import fn


def run():
    return fn.format_number(2.5, "#,##0.00").compile()
