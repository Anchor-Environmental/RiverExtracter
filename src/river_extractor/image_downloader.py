from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from rasterio.transform import from_bounds
from sentinelhub import (
    CRS,
    BBox,
    DataCollection,
    MimeType,
    SentinelHubRequest,
    bbox_to_dimensions,
)

EVALSCRIPT = """
//VERSION=3
function setup() {
    return {
        input: [{
            bands: ["B02", "B03", "B08", "B11", "B12","dataMask"]
        }],
        output: {
            bands: 6,
            sampleType: "FLOAT32"
        }
    };
}
function evaluatePixel(sample) {
    return [
        sample.B02,
        sample.B03,
        sample.B08,
        sample.B11,
        sample.B12,
        sample.dataMask
    ];
}
"""


def download_images(
    bbox: tuple[float, float, float, float],
    acquisition_datetime: str,
    config: Any,
    output_dir: str | Path = "downloads",
    resolution: int = 10,
    max_cloud_cover: float = 20.0,
) -> Path:
    """
    Download Sentinel-2 L2A imagery and store it as a GeoTIFF.

    Bands contained in GeoTIFF:

        Band 1 = B02 (Blue)
        Band 2 = B03 (Green)
        Band 3 = B08 (NIR)
        Band 4 = B11 (SWIR1)
        Band 5 = B12 (SWIR2)
        band 3 = dataMask


    Parameters:

    bbox:
        In the format (min_longitude, min_latitude, max_longitude, max_latitude)
        Note that the box coordinates must be listed top left then bottom right

    acquisition_datetime:
        In the ISO 8601 format: 2022-04-14T08:12:03Z

    config:
        Sentinel hub configuration object

    output_dir:
        Directory to save GeoTIFF file

    resolution:
        Requested spatial resolution in meters

    max_cloud_cover:
        Max permitted cloud cover from 0-100
        Cloud cover is computed by copernicus and your bbox may be smaller than the calculated sentinel cell size

    Returns pathlib.Path:
        Path to downloaded image.

    """

    validate_download_parameters(
        bbox=bbox,
        resolution=resolution,
        max_cloud_cover=max_cloud_cover,
    )

    acquisition_date = acquisition_datetime[:10]
    output_dir = Path(output_dir)
    output_file = output_dir / f"sentinel_image_{acquisition_date}.tif"

    image = request_sentinel2_image(
        bbox=bbox,
        acquisition_datetime=acquisition_datetime,
        config=config,
        resolution=resolution,
        max_cloud_cover=max_cloud_cover,
    )

    write_geotiff(image=image, bbox=bbox, output_file=output_file)

    print(f"Saved image to : {output_file}")

    return output_file


def request_sentinel2_image(
    bbox: tuple[float, float, float, float],
    acquisition_datetime: str,
    config: Any,
    resolution: int,
    max_cloud_cover: float,
) -> np.ndarray:
    """Request one SENTINEL2_L2A image from Sentinel Hub"""

    bbox_obj = BBox(bbox=bbox, crs=CRS.WGS84)

    width, height = bbox_to_dimensions(
        bbox_obj,
        resolution=resolution,
    )

    start_time, end_time = create_acquisition_window(acquisition_datetime)

    data_collection = DataCollection.SENTINEL2_L2A.define_from(
        "s212a_cdse", service_url=config.sh_base_url
    )

    request = SentinelHubRequest(
        evalscript=EVALSCRIPT,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=data_collection,
                time_interval=(start_time, end_time),
                maxcc=max_cloud_cover / 100.0,
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
        bbox=bbox_obj,
        size=(width, height),
        config=config,
    )

    print(f"Downloading Sentinel-2 imagery for {acquisition_datetime}...")

    data = request.get_data()

    if not data:
        raise RuntimeError(f"No Sentinel imagery returned for {acquisition_datetime}")

    image = np.asarray(data[0], dtype=np.float32)

    validate_image(image)

    return image


def create_acquisition_window(
    acquisition_datetime: str, tolerance_min: int = 1
) -> tuple[str, str]:
    """Create buffer arround acquisition datetime since sentinel hub requires a range"""
    normalised_datetime = acquisition_datetime.strip()

    if normalised_datetime.endswith("Z"):
        normalised_datetime = normalised_datetime[:-1] + "+00:00"

    try:
        acquisition_time = datetime.fromisoformat(normalised_datetime)
    except ValueError as exc:
        raise ValueError(
            f"Datetime must be a valid ISO 8601 datetime but recieved {acquisition_datetime!r}"
        ) from exc

    start_time = acquisition_time - timedelta(minutes=tolerance_min)
    end_time = acquisition_time + timedelta(minutes=tolerance_min)

    return start_time.isoformat(), end_time.isoformat()


def write_geotiff(
    image: np.ndarray,
    bbox: tuple[float, float, float, float],
    output_file: str | Path,
) -> Path:
    """Write image to GeoTIFF"""

    output_file = Path(output_file)

    min_lon, min_lat, max_lon, max_lat = bbox

    height, width, band_count = image.shape

    transform = from_bounds(
        min_lon,
        min_lat,
        max_lon,
        max_lat,
        width,
        height,
    )
    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": band_count,
        "dtype": rasterio.float32,
        "crs": "EPSG:4326",
        "transform": transform,
        "compress": "lzw",
    }
    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    with rasterio.open(output_file, "w", **profile) as dst:
        dst.write(np.moveaxis(image, -1, 0))

        dst.set_band_description(1, "B02 Blue")
        dst.set_band_description(2, "B03 Green")
        dst.set_band_description(3, "B08 NIR")
        dst.set_band_description(4, "B11 SWIR1")
        dst.set_band_description(5, "B12 SWIR2")
        dst.set_band_description(6, "DataMask")

    return output_file


def validate_download_parameters(
    bbox: tuple[float, float, float, float],
    resolution: int,
    max_cloud_cover: float,
) -> None:
    """Validate the user supplied download parameters"""

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

    if resolution <= 0:
        raise ValueError(f"Resolution must be greater than 0: {resolution}")

    if not 0 <= max_cloud_cover <= 100:
        raise ValueError(f"Max cloud cover is outside [0, 100]: {max_cloud_cover}")


def validate_image(image: np.ndarray) -> None:
    """Validate the array returned by sentinelhub"""

    if image.ndim != 3:
        raise RuntimeError(
            f"Expected a 3-dimensional Sentinel array but recieved: {image.shape}"
        )

    expected_band_count = 6
    actual_band_count = image.shape[-1]

    if expected_band_count != actual_band_count:
        raise RuntimeError(
            f"Expected {expected_band_count} Sentinel bands but recieved {actual_band_count}"
        )

    if image.shape[0] == 0 or image.shape[1] == 0:
        raise RuntimeError("Sentinel Hub returned empty array")
