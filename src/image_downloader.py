from datetime import datetime, timedelta
from pathlib import Path

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


# ------------------------------------------------------------------
# Sentinel download
# ------------------------------------------------------------------
def download_sentinel2(
    bbox: tuple[float, float, float, float],
    start_date: str,
    end_date: str,
    config,
    output_file: Path,
    resolution: int = 10,
    max_cloud_cover: float = 20,
) -> Path:
    """
    Download Sentinel-2 L2A imagery.
    Output GeoTIFF:
        Band 1 = B03 (Green)
        Band 2 = B08 (NIR)
        band 3 = dataMask
    """
    bbox_obj = BBox(bbox=bbox, crs=CRS.WGS84)
    width, height = bbox_to_dimensions(
        bbox_obj,
        resolution=resolution,
    )
    evalscript = """
    //VERSION=3
    function setup() {
        return {
            input: [{
                bands: ["B03", "B08", "dataMask"]
            }],
            output: {
                bands: 3,
                sampleType: "FLOAT32"
            }
        };
    }
    function evaluatePixel(sample) {
        return [
            sample.B03,
            sample.B08,
            sample.dataMask
        ];
    }
    """
    print("Config ID:", id(config))
    print("Base URL:", config.sh_base_url)
    print("Collection URL:", DataCollection.SENTINEL2_L2A.service_url)

    dt = datetime.fromisoformat(start_date.replace("Z", ""))

    start = (dt - timedelta(minutes=1)).isoformat()
    end = (dt + timedelta(minutes=1)).isoformat()

    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A.define_from(
                    "s212a_cdse", service_url=config.sh_base_url
                ),
                time_interval=(start, end),
                maxcc=max_cloud_cover / 100.0,
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
        bbox=bbox_obj,
        size=(width, height),
        config=config,
    )

    print("Downloading Sentinel-2 imagery...")
    data = request.get_data()
    if len(data) == 0:
        raise RuntimeError("No Sentinel imagery returned.")
    image = data[0]
    min_lon, min_lat, max_lon, max_lat = bbox
    transform = from_bounds(
        min_lon,
        min_lat,
        max_lon,
        max_lat,
        image.shape[1],
        image.shape[0],
    )
    profile = {
        "driver": "GTiff",
        "height": image.shape[0],
        "width": image.shape[1],
        "count": 3,
        "dtype": rasterio.float32,
        "crs": "EPSG:4326",
        "transform": transform,
        "compress": "lzw",
    }
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(output_file, "w", **profile) as dst:
        dst.write(np.moveaxis(image, -1, 0))
    print(f"Saved Sentinel image to: {output_file}")
    return output_file


def main(
    bbox: tuple[float, float, float, float],
    start_date: str,
    end_date: str,
    config,
    output_dir: str = "downloads",
    resolution: int = 10,
    max_cloud_cover: float = 20.0,
) -> Path:
    output_file = Path(output_dir) / f"sentinel_image_{start_date[0:10]}.tif"

    download_sentinel2(
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        config=config,
        output_file=output_file,
        resolution=resolution,
        max_cloud_cover=max_cloud_cover,
    )
    return output_file
