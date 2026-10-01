from datetime import time
from mlclient.functions.xqy import fn


def run():
    return fn.date_time(fn.current_date(), time(3, 4, 5)).compile()
