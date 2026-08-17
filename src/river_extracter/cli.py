import argparse
from collections.abc import Sequence

from workflow import run_workflow

DEFAULT_BBOX = (31.1482, -29.5482, 31.2075, -29.5882)


def build_parser() -> argparse.ArgumentParser:
    """Create and configure the command line interface"""

    parser = argparse.ArgumentParser(
        prog="RiverExtracter",
        description=("Download and process satellite imagery."),
    )

    parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        metavar=("MIN_X", "MIN_Y", "MAX_X", "MAX_Y"),
        default=DEFAULT_BBOX,
        help=("Bounding box coordinates in the order " "MIN_X MIN_Y MAX_X MAX_Y."),
    )

    parser.add_argument(
        "--start-date",
        default="2022-04-14",
        help="Start date in YYYY-MM-DD",
    )

    parser.add_argument(
        "--end-date",
        default="2022-04-15",
        help="Start date in YYYY-MM-DD",
    )

    parser.add_argument(
        "--max-cloud-cover",
        type=float,
        default=20.0,
        help="Maximum permitted cloud cover - default: 20.0",
    )

    parser.add_argument(
        "--processing-threshold",
        type=float,
        default=0.01,
        help="NDWI Image processing threshold - default: 0.01",
    )

    parser.add_argument(
        "--download-dir",
        default="downloads",
        help="Path to store downloaded images.",
    )

    parser.add_argument(
        "--output-dir",
        default="output",
        help="Path to store processed images.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run river extracter tool CLI"""

    parser = build_parser()
    args = parser.parse_args(argv)

    run_workflow(
        bbox=tuple(args.bbox),
        start_date=args.start_date,
        end_date=args.end_date,
        max_cloud_cover=args.max_cloud_cover,
        processing_threshold=args.processing_threshold,
        download_dir=args.download_dir,
        output_dir=args.output_dir,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
