from mlclient.xquery import fn


def run():
    return fn.current_date_time().compile()
