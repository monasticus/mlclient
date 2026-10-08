from mlclient.xquery import fn


def run():
    return fn.adjust_time_to_timezone(fn.current_time()).compile()
