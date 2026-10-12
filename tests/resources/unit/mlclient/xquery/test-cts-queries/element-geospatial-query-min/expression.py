"""Serialization through the public CTS builder.

Native constructor: ``cts:element-geospatial-query``.
"""

from mlclient.xquery import cts


def run():
    return cts.element_geospatial_query(
        "origin",
        [
            cts.box(1.5, 2, 3, 4),
            cts.circle(5, cts.point(10, 20)),
            cts.polygon(
                [cts.point(0, 0), cts.point(0, 1), cts.point(1, 1), cts.point(0, 0)],
            ),
        ],
    )
