from mlclient.functions.xqy import cts, fn


def run():
    return fn.format_number(
        2.5, "#,##0.00", decimal_format_name=fn.string(cts.search().index(1)),
    ).compile()
