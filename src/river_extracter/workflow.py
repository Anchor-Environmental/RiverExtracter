from pathlib import Path
from typing import Any

from config_creator import main as create_config
from image_downloader import main as download_images
from image_lister_offline import main as list_offline_images
from image_lister_online import main as list_online_images
from image_processor import main as process_images

# (31.1482, -29.5482, 31.2075, -29.5882)


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
    bbox=tuple[float, float, float, float],
    start_date="2022-04-20",
    end_date="2022-04-30",
    max_cloud_cover=20.0,
    processing_threshold=0.01,
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

        acquisition_date = get_acquisition_date(acquisition)

        if acquisition_date in offline_dates:
            print(f"Skipping {acquisition_date}: already downloaded.")
            continue

        acquisition_datetime = acquisition["properties"]["datetime"]

        print(f"Downloading acquisition from {acquisition_datetime}.")

        download_images(
            bbox=bbox,
            start_date=acquisition_datetime,
            end_date=acquisition_datetime,
            config=config,
        )

    print("Downloading complete.")

    all_acquisitions = list_offline_images(download_dir)

    for filename in all_acquisitions:
        input_path = download_dir / filename

        print(f"Processing {input_path}.")

        process_images(
            input_file_path=input_path,
            output_dir=output_dir,
            threshold=processing_threshold,
        )
    print("Workflow complete.")


if __name__ == "__main__":
    main()
