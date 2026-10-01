from datetime import time
from mlclient.functions.xqy import cts, fn


def run():
    return fn.adjust_time_to_timezone(
        time(3, 4, 5), timezone=fn.string(cts.search().index(1)),
    ).compile()
