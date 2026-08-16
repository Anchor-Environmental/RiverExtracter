from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio


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
    filename: str,
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
    ax1.set_title(f"NDWI {filename}")
    ax2.imshow(
        river_mask,
        cmap="Blues",
    )
    ax2.set_title(f"Extracted Water {filename}")
    plt.tight_layout()
    plt.show()


# ------------------------------------------------------------------
# Check avaliable imagery
# ------------------------------------------------------------------


# ------------------------------------------------------------------
# Public pipeline entry point
# ------------------------------------------------------------------
def main(
    input_file_path: str = "downloads/exampleimage.tif",
    output_dir: str = "output",
    threshold: float = 0.0,
) -> Path:
    """
    Main function called from main.py
    """

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    satellite_file = input_file_path
    extracted_file = output_path / input_file_path.name

    ndwi, river_mask = extract_water(
        satellite_file=satellite_file,
        output_file=extracted_file,
        threshold=threshold,
    )
    plot_results(ndwi, river_mask, input_file_path.name)
    print("Processing complete.")
