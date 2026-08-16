import argparse
from collections.abc import Sequence
from pathlib import Path

from config_creator import main as create_config
from image_downloader import main as download_images
from image_lister_offline import main as list_offline_images
from image_lister_online import main as list_online_images
from image_processor import main as process_images


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="RiverExtracter",
        description="Download and process satellite imagery.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    process_parser = subparsers.add_parser(
        "process",
        help="Process an existing raster.",
    )
    process_parser.add_argument(
        "input",
        help="Path to the input raster.",
    )
    process_parser.add_argument(
        "output",
        help="Path for the processed raster.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "process":
        output_path = process_raster(args.input, args.output)
        print(f"Saved processed raster to: {output_path}")
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


def main() -> None:
    bbox = (31.1482, -29.5482, 31.2075, -29.5882)
    start_date = "2022-04-20"
    end_date = "2022-04-30"
    max_cloud_cover = 20.0
    processing_threshold = 0.01
    config = create_config()

    online_acquisitions = list_online_images(
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        max_cloud_cover=max_cloud_cover,
        config=config,
    )

    offline_acquisitions = list_offline_images("./downloads")
    offline_acquisitions_clean = [
        img.replace("sentinel_image_", "").replace(".tif", "")
        for img in offline_acquisitions
    ]

    for val in online_acquisitions:
        if val["properties"]["datetime"][0:10] in offline_acquisitions_clean:
            continue
        else:
            print(f"file {val["properties"]["datetime"]} needs to be downloaded")
            path = download_images(
                bbox=bbox,
                start_date=val["properties"]["datetime"],
                end_date=val["properties"]["datetime"],
                config=config,
            )

    print(f"Downloading complete.")

    all_acquisitions = list_offline_images("./downloads")

    for file in all_acquisitions:
        filepath = Path("downloads") / file

        process_images(
            input_file_path=filepath,
            output_dir="output",
            threshold=processing_threshold,
        )


if __name__ == "__main__":
    main()
