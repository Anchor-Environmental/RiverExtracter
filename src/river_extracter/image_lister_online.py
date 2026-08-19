from typing import Any

from sentinelhub import CRS, BBox, DataCollection, SentinelHubCatalog, SHConfig


def list_online_images(
    bbox: tuple[float, float, float, float],
    start_date: str,
    end_date: str,
    max_cloud_cover: float,
    config: SHConfig,
) -> list[dict[str, Any]]:
    """
    List avaliable Sentinel-2 L2A images

    Parameters:
        bbox:
            In the format (min_longitude, min_latitude, max_longitude, max_latitude)
            Note that the box coordinates must be listed top left then bottom right

        start_date:
            Begining of the search interval
            Must be in ISO 8601 or datetime

        end_date:
            End of the search interval
            Must be in ISO 8601 or datetime

        max_cloud_cover:
            Maximum permitted cloud cover percentage [0, 100]

        config:
            Sentinel hub configuration

    Returns:
        Catalogue of avaliable acquisitions in the format list[dict[str, Any]]

    """

    validate_search_parameters(
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        max_cloud_cover=max_cloud_cover,
    )

    bbox_obj = BBox(
        bbox=bbox,
        crs=CRS.WGS84,
    )

    catalog = SentinelHubCatalog(config=config)

    collection = DataCollection.SENTINEL2_L2A.define_from(
        "s212a_cdse",
        service_url=config.sh_base_url,
    )

    search_results = catalog.search(
        collection=collection,
        bbox=bbox_obj,
        time=(start_date, end_date),
        filter=f"eo:cloud_cover <= {max_cloud_cover}",
    )

    acquisitions = list(search_results)

    return sorted(
        acquisitions,
        key=get_acquisitions_datetime,
    )


def get_acquisitions_datetime(
    acquisition: dict[str, Any],
) -> str:
    """Return the datetime from a Sentinel catalog acquisition"""

    try:
        return acquisition["properties"]["datetime"]
    except KeyError as exc:
        raise ValueError("Acquisition does not contain properties.datetime") from exc


def validate_search_parameters(
    bbox: tuple[float, float, float, float],
    start_date: str,
    end_date: str,
    max_cloud_cover: float,
) -> None:
    """Validate the Sentinel Hub search parameters"""

    if len(bbox) != 4:
        raise ValueError("bbox must contain exactly four coordinates")

    min_lon, min_lat, max_lon, max_lat = bbox

    if min_lon >= max_lon:
        raise ValueError("Minimum longitude must be smaller than maximum longitude")

    if min_lat >= max_lat:
        raise ValueError("Minimum latitude must be smaller than maximum latitude")

    if not -180 <= min_lon <= 180:
        raise ValueError(f"Minimum longitude is outside [-180, 180]: {min_lon}")

    if not -180 <= max_lon <= 180:
        raise ValueError(f"Maximum longitude is outside [-180, 180]: {max_lon}")

    if not -90 <= min_lat <= 90:
        raise ValueError(f"Minimum latitude is outside [-90, 90]: {min_lat}")

    if not -90 <= max_lat <= 90:
        raise ValueError(f"Maximum latitude is outside [-90, 90]: {max_lat}")

    if not start_date:
        raise ValueError("Start date must not be empty")

    if not end_date:
        raise ValueError("End date must not be empty")

    if not 0 <= max_cloud_cover <= 100:
        raise ValueError(f"Max cloud cover is outside [0, 100]: {max_cloud_cover}")
