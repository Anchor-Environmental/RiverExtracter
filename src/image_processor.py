import rasterio
import numpy as np
import matplotlib.pyplot as plt
import os

def main() -> None: # 1. Open the multi-band satellite image (e.g., Sentinel-2 or Landsat)
  with rasterio.open("./images/satellite_image.tif") as src:
      # Assuming Band 3 is Green and Band 8 is NIR (standard for Sentinel-2)
      green = src.read(3).astype(float)
      nir = src.read(8).astype(float)
      meta = src.meta.copy()

# 2. Prevent division by zero errors
  np.seterr(divide='ignore', invalid='ignore')

# 3. Calculate NDWI
  ndwi = (green - nir) / (green + nir)

# 4. Apply a threshold to isolate water 
# Water pixels usually have NDWI values greater than 0.0
  river_mask = np.where(ndwi > 0.0, 1, 0).astype(np.uint8)

# 5. Save the extracted river mask to a new GeoTIFF
  meta.update(driver="GTiff", dtype=rasterio.uint8, count=1)
  with rasterio.open("extracted_river.tif", "w", **meta) as dst:
    dst.write(river_mask, 1)

# 6. Plot the results
  fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
  ax1.imshow(ndwi, cmap="RdBu")
  ax1.set_title("NDWI Index Map")
  ax2.imshow(river_mask, cmap="Blues")
  ax2.set_title("Extracted River Mask")
  plt.show()