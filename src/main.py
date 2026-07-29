from image_processor import main as process_image


def main() -> None:
    bbox = (31.1482, -29.5482, 31.2075, -29.5882)

    process_image(
        bbox=bbox,
        start_date="2023-01-01",
        end_date="2023-01-30",
        output_dir="output",
        threshold=0.0,
        max_cloud_cover=20.0,
    )


if __name__ == "__main__":
    main()
