from mlclient.xquery import fn


def run():
    return fn.format_date_time(
        fn.current_date_time(), "[Y0001]-[M01]-[D01]T[H01]:[m01]:[s01]",
    ).compile()
