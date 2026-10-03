from mlclient.functions.xqy import fn


def run():
    return fn.format_time(fn.current_time(), "[H01]:[m01]:[s01]").compile()
