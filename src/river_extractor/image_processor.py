from __future__ import annotations

from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
import rasterio

WaterExtractionMethod = Literal[
    "aweish",
    "ndwi",
]


def process_image(
    input_file_path: str | Path,
    output_dir: str | Path = "output",
    threshold: float = 0.01,
    method: WaterExtractionMethod = "aweish",
    show_plot: bool = False,
) -> Path:
    """
    Calculate NDWI or AWEISH and generate a river/estuary mask.

    Parameters:

        input_file_path:
            Path to Sentinel-2 GeoTIFF containing the following bands:

            Band 1 = B02 (BLUE)
            Band 2 = B03 (GREEN)
            Band 3 = B08 (NIR)
            Band 4 = B11 (SWIR1)
            Band 5 = B12 (SWIR2)
            Band 6 = dataMask

        output_dir:
            Directory to save GeoTIFF file

        threshold:
            NDWI threshold above which a pixel is classified as water

        method:
            Water extraction method, only "aweish" and "ndwi" are supported right now. The default is "aweish"

        show_plot:
            Enable or disable matplotlib plotting of GeoTIFF

    Returns:

        pathlib.Path - path to generated water-mask GeoTIFF

    """

    input_file_path = Path(input_file_path)
    output_dir = Path(output_dir)

    validate_input_file(input_file_path)
    validate_method(method)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = output_dir / f"{input_file_path.stem}_{method}_water_mask.tif"

    water_index, river_mask = extract_water(
        satellite_file=input_file_path,
        output_file=output_file,
        threshold=threshold,
        method=method,
    )

    if show_plot:
        plot_results(
            water_index=water_index,
            river_mask=river_mask,
            filename=input_file_path.name,
            method=method,
        )

    print(f"Processing complete: {output_file}")

    return output_file


def extract_water(
    satellite_file: str | Path,
    output_file: str | Path,
    threshold: float = 0.01,
    method: WaterExtractionMethod = "aweish",
) -> tuple[np.ndarray, np.ndarray]:
    """
        Calculates a water index and writes a binary water mask geotiff


        Parameters:

            satellite_file:
                Path to GeoTIFF file containing required bands Green, NIR and dataMask

            output_file:
                Output watermask GeoTIFF

            method:
                AWEIsh is the default method.

                NDWI is calculated as (green - NIR) / (green + NIR)
                Pixels greater than threshold are classified as water



            threshold:
                Float determining pixel value for water classification
    method=method,
        Returns:

            tuple[np.ndarray, np.ndarray]
            NDWI array and binary watermask array

    """

    satellite_file = Path(satellite_file)
    output_file = Path(output_file)

    validate_method(method)

    with rasterio.open(satellite_file) as src:

        validate_raster(
            src=src,
            method=method,
        )

        if method == "aweish":
            blue = src.read(1).astype(np.float32)
            green = src.read(2).astype(np.float32)
            nir = src.read(3).astype(np.float32)
            swir1 = src.read(4).astype(np.float32)
            swir2 = src.read(5).astype(np.float32)

            water_index = calculate_aweish(
                blue=blue,
                green=green,
                nir=nir,
                swir1=swir1,
                swir2=swir2,
            )

        elif method == "ndwi":

            green = src.read(2).astype(np.float32)
            nir = src.read(3).astype(np.float32)

            water_index = calculate_ndwi(
                green=green,
                nir=nir,
            )

        output_profile = src.profile.copy()

    river_mask = create_water_mask(
        water_index=water_index,
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
            f"{method.upper()} water mask",
        )
    print(f"Saved river mask to: {output_file}")

    return water_index, river_mask


def calculate_aweish(
    blue: np.ndarray,
    green: np.ndarray,
    nir: np.ndarray,
    swir1: np.ndarray,
    swir2: np.ndarray,
) -> np.ndarray:
    """
    Calculate the Automated Water Extraction Index with SHadows

    Calculated as:
        Blue
        + 2.5 * Green
        - 1.5 * (NIR + SWIR1)
        - 0.25 * SWIR2
    """
    arrays = {
        "blue": blue,
        "green": green,
        "nir": nir,
        "swir1": swir1,
        "swir2": swir2,
    }

    validate_array_shapes(arrays)

    return (blue + 2.5 * green - 1.5 * (nir + swir1) - 0.25 * swir2).astype(np.float32)


def calculate_ndwi(
    green: np.ndarray,
    nir: np.ndarray,
) -> np.ndarray:
    """
    Calculate NDWI from green and NIR bands

    Assign pixels with 0 denominator as NaN
    """

    validate_array_shapes(
        {
            "green": green,
            "nir": nir,
        }
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
    water_index: np.ndarray,
    threshold: float,
) -> np.ndarray:
    """
    Create binary of water mask

    Output values: 0 - Not water
                   1 - Water
    """
    water_pixels = np.isfinite(water_index) & (water_index > threshold)

    return water_pixels.astype(np.uint8)


def plot_results(
    water_index: np.ndarray,
    river_mask: np.ndarray,
    filename: str,
    method: WaterExtractionMethod,
) -> None:
    """
    Display matplotlib figure of NDWI and Water Mask
    """

    figure, (index_ax, watermask_ax) = plt.subplots(
        1,
        2,
        figsize=(12, 6),
    )
    index_image = index_ax.imshow(
        water_index,
        cmap="RdBu",
    )

    index_ax.set_title(f"method.upper(): {filename}")
    index_ax_ax.set_axis_off()

    figure.colorbar(
        index_image,
        ax=index_ax,
        label=method.upper(),
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


def validate_method(
    method: str,
) -> None:
    """
    Validate the requested water-extraction method
    """
    supported_methods = {
        "aweish",
        "ndwi",
    }

    if method not in supported_methods:
        supported_values = ", ".join(supported_methods)

        raise ValueError(
            f"Unsupported extraction method: {method!r}."
            f"Supported methods are: {supported_values}"
        )


def validate_array_shapes(
    arrays: dict[str, np.ndarray],
) -> None:
    """Validate that all bands have the same shape arrays"""
    shapes = {name: array.shape for name, array in arrays.items()}
    unique_shapes = set(shapes.values())

    if len(unique_shapes) != 1:
        shape_description = ", ".join(
            f"{name}={shape}" for name, shape in shapes.items()
        )

        raise ValueError(
            f"All spectral bands must have the same shape. However, recieved: {shape_description}"
        )


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


def validate_raster(
    src: rasterio.io.DatasetReader,
    method: WaterExtractionMethod,
) -> None:
    """
    Validate that the raster contains the  required bands
    """

    if src.width <= 0 or src.height <= 0:
        raise ValueError("The input raster has invalid dimensions")

    required_band_counts = {
        "ndwi": 3,
        "aweish": 5,
    }

    if src.count < required_band_counts[method]:
        raise ValueError(
            f"The {method.upper()} method requires {required_band_count}"
            f"The input raster has {src.count} bands"
        )
