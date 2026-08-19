from pathlib import Path
from typing import Any

from config_creator import create_config
from image_downloader import download_images
from image_lister_offline import list_offline_images
from image_lister_online import list_online_images
from image_processor import process_image

# (31.1482, -29.5882, 31.2075, -29.5482)


def get_acquisition_date(acquisition: dict[str, Any]) -> str:
    """Extract YYYY-MM-DD from a downloaded sentinel file.
    Currenlty uses the common text "sentinel_image_" from the downloading
    the image downloader module
    """
    try:
        acquisition_datetime = acquisition["properties"]["datetime"]
    except KeyError as exc:
        raise ValueError("Acquisition does not contain properties.datetime.") from exc
    return acquisition_datetime[:10]


def run_workflow(
    bbox: tuple[float, float, float, float],
    start_date: str,
    end_date: str,
    max_cloud_cover: float = 20.0,
    processing_threshold: float = 0.01,
    download_dir: str | Path = "downloads",
    output_dir: str | Path = "output",
) -> None:
    """Download sentinel imagery and process local aquisitions"""

    download_dir = Path(download_dir)
    output_dir = Path(output_dir)

    download_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    config = create_config()

    online_acquisitions = list_online_images(
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        max_cloud_cover=max_cloud_cover,
        config=config,
    )

    offline_acquisitions = list_offline_images(download_dir)

    offline_dates = [
        filename.replace("sentinel_image_", "").replace(".tif", "")
        for filename in offline_acquisitions
    ]

    for acquisition in online_acquisitions:

        acquisition_datetime = acquisition["properties"]["datetime"]
        acquisition_date = acquisition_datetime[:10]

        if acquisition_date in offline_dates:
            print(f"Skipping {acquisition_date}: already downloaded.")
            continue

        print(f"Downloading acquisition from {acquisition_date}.")

        download_images(
            bbox=bbox,
            acquisition_datetime=acquisition_datetime,
            config=config,
            output_dir=download_dir,
            max_cloud_cover=max_cloud_cover,
        )

    print("Downloading complete.")

    all_acquisitions = list_offline_images(download_dir)

    for filename in all_acquisitions:
        input_path = download_dir / filename

        print(f"Processing {input_path}.")

        process_image(
            input_file_path=input_path,
            output_dir=output_dir,
            threshold=processing_threshold,
            show_plot=True,
        )
    print("Workflow complete.")


if __name__ == "__main__":
    main()
