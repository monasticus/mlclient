from datetime import time
from mlclient.functions.xqy import cts, fn


def run():
    return fn.format_time(time(3, 4, 5), fn.string(cts.search().pos(1))).compile()
