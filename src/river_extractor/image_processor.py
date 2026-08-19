from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio


def process_image(
    input_file_path: str | Path,
    output_dir: str | Path = "output",
    threshold: float = 0.01,
    show_plot: bool = False,
) -> Path:
    """
    Calculate NDWI and generate a river/estuary mask.

    Parameters:

        input_file_path:
            Path to Sentinel-2 GeoTIFF containing the following bands:

            Band 1 = B03 (Green)
            Band 2 = B08 (NIR)
            Band 3 = dataMask

        output_dir:
            Directory to save GeoTIFF file

        threshold:
            NDWI threshold above which a pixel is classified as water

        show_plot:
            Enable or disable matplotlib plotting of GeoTIFF

    Returns:

        pathlib.Path - path to generated water-mask GeoTIFF

    """

    input_file_path = Path(input_file_path)
    output_dir = Path(output_dir)

    validate_input_file(input_file_path)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = output_dir / f"{input_file_path.stem}_water_mask.tif"

    ndwi, river_mask = extract_water(
        satellite_file=input_file_path,
        output_file=output_file,
        threshold=threshold,
    )

    if show_plot:
        plot_results(
            ndwi=ndwi,
            river_mask=river_mask,
            filename=input_file_path.name,
        )

    print(f"Processing complete: {output_file}")

    return output_file


def extract_water(
    satellite_file: str | Path,
    output_file: str | Path,
    threshold: float = 0.01,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Calculates NDWI and writes a binary water mask geotiff

    NDWI is calculated as (green - NIR) / (green + NIR)
    Pixels greater than threshold are classified as water

    Parameters:

        satellite_file:
            Path to GeoTIFF file containing required bands Green, NIR and dataMask

        output_file:
            Output watermask GeoTIFF

        threshold:
            Float determining pixel value for water classification

    Returns:

        tuple[np.ndarray, np.ndarray]
        NDWI array and binary watermask array

    """

    satellite_file = Path(satellite_file)
    output_file = Path(output_file)

    with rasterio.open(satellite_file) as src:

        validate_raster(src)

        green = src.read(1).astype(np.float32)
        nir = src.read(2).astype(np.float32)

        output_profile = src.profile.copy()

    ndwi = calculate_ndwi(
        green=green,
        nir=nir,
    )

    river_mask = create_water_mask(
        ndwi=ndwi,
        threshold=threshold,
    )

    output_profile.pop("photometric", None)
    output_profile.pop("interleave", None)

    output_profile.update(
        driver="GTiff",
        dtype=rasterio.uint8,
        count=1,
        nodata=None,
        compress="lzw",
    )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with rasterio.open(output_file, "w", **output_profile) as dst:
        dst.write(river_mask, 1)
        dst.set_band_description(
            1,
            "NDWI water mask",
        )
    print(f"Saved river mask to: {output_file}")

    return ndwi, river_mask


def calculate_ndwi(
    green: np.ndarray,
    nir: np.ndarray,
) -> np.ndarray:
    """
    Calculate NDWI from green and NIR bands

    Assign pixels with 0 denominator as NaN
    """
    if green.shape != nir.shape:
        raise ValueError(
            "Green and NIR arrays must have the same shape."
            f"Recieved green: {green.shape} and nir: {nir.shape}"
        )

    denominator = green + nir

    ndwi = np.full(
        green.shape,
        np.nan,
        dtype=np.float32,
    )

    np.divide(
        green - nir,
        denominator,
        out=ndwi,
        where=denominator != 0,
    )

    return ndwi


def create_water_mask(
    ndwi: np.ndarray,
    threshold: float,
) -> np.ndarray:
    """
    Create binary of water mask

    Output values: 0 - Not water
                   1 - Water
    """
    water_pixels = np.isfinite(ndwi) & (ndwi > threshold)

    return water_pixels.astype(np.uint8)


def plot_results(
    ndwi: np.ndarray,
    river_mask: np.ndarray,
    filename: str,
) -> None:
    """
    Display matplotlib figure of NDWI and Water Mask
    """

    figure, (ndwi_ax, watermask_ax) = plt.subplots(
        1,
        2,
        figsize=(12, 6),
    )
    ndwi_image = ndwi_ax.imshow(
        ndwi,
        cmap="RdBu",
        vmin=-1,
        vmax=1,
    )

    ndwi_ax.set_title(f"NDWI {filename}")
    ndwi_ax.set_axis_off()

    figure.colorbar(
        ndwi_image,
        ax=ndwi_ax,
        label="NDWI",
        fraction=0.046,
        pad=0.04,
    )

    watermask_ax.imshow(
        river_mask,
        cmap="Blues",
        vmin=0,
        vmax=1,
    )

    watermask_ax.set_title(f"Extracted Water {filename}")

    watermask_ax.set_axis_off()

    figure.tight_layout()

    plt.show()

    plt.close(figure)


def validate_input_file(input_file_path: Path) -> None:
    """Validate the supplied input path"""

    if not input_file_path.exists():
        raise FileNotFoundError(f"Satellite image does not exist: {input_file_path}")

    if not input_file_path.is_file():
        raise ValueError(f"Satellite image path is not a file: {input_file_path}")

    if input_file_path.suffix.lower() not in {
        ".tif",
        ".tiff",
    }:
        raise ValueError(
            f"Satellite image does not have a .tif or .tiff extension {input_file_path}"
        )


def validate_raster(source: rasterio.io.DatasetReader) -> None:
    """
    Validate that the raster contains the two required bands
    Band 1: Green
    Band 2: NIR
    """

    required_band_count = 2

    if source.count < required_band_count:
        raise ValueError(
            f"The input raster has {source.count} bands, less than the required band cound of {required_band_count}"
        )

    if source.width <= 0 or source.height <= 0:
        raise ValueError("The input raster has invalid dimensions")
