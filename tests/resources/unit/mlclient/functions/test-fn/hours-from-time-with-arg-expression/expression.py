from mlclient.functions.xqy import fn


def run():
    return fn.hours_from_time(fn.current_time()).compile()
