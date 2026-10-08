from datetime import time
from mlclient.xquery import cts, fn


def run():
    return fn.format_time(time(3, 4, 5), fn.string(cts.search().pos(1))).compile()
