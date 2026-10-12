"""Public compilation and native serialization of GeospatialRegionQuery."""

from mlclient.xquery import cts


def run():
    return cts.geospatial_region_query(
        cts.geospatial_region_path_reference(
            "/report/region",
            options=["unchecked", "coordinate-system=wgs84"],
            geohash_precision=4,
            units="km",
            invalid_values="reject",
        ),
        "intersects",
        cts.box(1, 2, 3, 4),
    )
