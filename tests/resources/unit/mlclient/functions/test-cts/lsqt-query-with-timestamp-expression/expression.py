from mlclient.functions.xqy import cts, fn


def run():
    return cts.lsqt_query("temporal", timestamp=fn.current_date_time()).compile()
