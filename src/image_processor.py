from __future__ import annotations
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from config import CDSE_CLIENT_ID, CDSE_CLIENT_SECRET
from sentinelhub import (
    BBox,
    CRS,
    SHConfig,
    DataCollection,
    SentinelHubRequest,
    MimeType,
    MosaickingOrder,
    bbox_to_dimensions,
)
# ------------------------------------------------------------------
# Copernicus Data Space configuration
# ------------------------------------------------------------------


def get_config() -> SHConfig:
    TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    )
    BASE_URL = "https://sh.dataspace.copernicus.eu"
    """
    Reads credentials from environment variables.
    Required:
        CDSE_CLIENT_ID
        CDSE_CLIENT_SECRET
    """
    config = SHConfig()
    client_id = CDSE_CLIENT_ID
    client_secret = CDSE_CLIENT_SECRET

    
    config.sh_client_id = client_id
    config.sh_client_secret = client_secret
    config.sh_base_url = BASE_URL
    config.sh_token_url = TOKEN_URL

    config.save("cdse_temp")
    
    return SHConfig("cdse_temp")

# ------------------------------------------------------------------
# Sentinel download
# ------------------------------------------------------------------
def download_sentinel2(
    bbox: tuple[float, float, float, float],
    start_date: str,
    end_date: str,
    output_file: Path,
    resolution: int = 10,
    max_cloud_cover: float = 0,
) -> Path:
    """
    Download Sentinel-2 L2A imagery.
    Output GeoTIFF:
        Band 1 = B03 (Green)
        Band 2 = B08 (NIR)
    """
    config = get_config()
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
                bands: ["B03", "B08"]
            }],
            output: {
                bands: 2,
                sampleType: "FLOAT32"
            }
        };
    }
    function evaluatePixel(sample) {
        return [
            sample.B03,
            sample.B08
        ];
    }
    """
    print("Config ID:", id(config))
    print("Base URL:", config.sh_base_url)
    print("Collection URL:", DataCollection.SENTINEL2_L2A.service_url)

    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A.define_from("s212a_cdse", service_url=config.sh_base_url),
                time_interval=(start_date, end_date),
                mosaicking_order=MosaickingOrder.LEAST_CC,
                maxcc=max_cloud_cover / 100.0,
            )
        ],
        responses=[
            SentinelHubRequest.output_response(
                "default",
                MimeType.TIFF
            )
        ],
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
        "count": 2,
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

# ------------------------------------------------------------------
# NDWI water extraction
# ------------------------------------------------------------------
def extract_water(
    satellite_file: Path,
    output_file: Path,
    threshold: float = 0,
):
    """
    Calculate NDWI and generate a river/estuary mask.
    """
    with rasterio.open(satellite_file) as src:
        # Band 1 = B03 Green
        green = src.read(1).astype(np.float32)
        # Band 2 = B08 NIR
        nir = src.read(2).astype(np.float32)
        meta = src.meta.copy()
    np.seterr(divide="ignore", invalid="ignore")
    ndwi = (green - nir) / (green + nir)
    river_mask = np.where(
        ndwi > threshold,
        1,
        0,
    ).astype(np.uint8)
    meta.update(
        driver="GTiff",
        dtype=rasterio.uint8,
        count=1,
    )
    with rasterio.open(output_file, "w", **meta) as dst:
        dst.write(river_mask, 1)
    print(f"Saved river mask to: {output_file}")
    return ndwi, river_mask

# ------------------------------------------------------------------
# Plotting
# ------------------------------------------------------------------
def plot_results(
    ndwi: np.ndarray,
    river_mask: np.ndarray,
) -> None:
    fig, (ax1, ax2) = plt.subplots(
        1,
        2,
        figsize=(12, 6),
    )
    ax1.imshow(
        ndwi,
        cmap="RdBu",
    )
    ax1.set_title("NDWI")
    ax2.imshow(
        river_mask,
        cmap="Blues",
    )
    ax2.set_title("Extracted Water")
    plt.tight_layout()
    plt.show()

# ------------------------------------------------------------------
# Public pipeline entry point
# ------------------------------------------------------------------
def main(
    bbox: tuple[float, float, float, float],
    start_date: str,
    end_date: str,
    output_dir: str = "output",
    threshold: float = 0.0,
    resolution: int = 5,
    max_cloud_cover: float = 0.0,
) -> None:
    """
    Main function called from main.py
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    satellite_file = output_path / "satellite_image.tif"
    extracted_file = output_path / "extracted_river.tif"
    download_sentinel2(
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        output_file=satellite_file,
        resolution=resolution,
        max_cloud_cover=max_cloud_cover,
    )
    ndwi, river_mask = extract_water(
        satellite_file=satellite_file,
        output_file=extracted_file,
        threshold=threshold,
    )
    plot_results(
        ndwi,
        river_mask,
    )
    print("Processing complete.")