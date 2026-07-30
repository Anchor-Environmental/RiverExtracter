from image_lister import main as list_image
from image_processor import main as process_image


def main() -> None:
    bbox = (31.1482, -29.5482, 31.2075, -29.5882)
    start_date = "2024-01-01"
    end_date = "2025-01-01"

    list_image(
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        max_cloud_cover=20.0,
    )

    # process_image(
    #     bbox=bbox,
    #     start_date="2024-01-01",
    #     end_date="2024-01-30",
    #     output_dir="output",
    #     threshold=0.0,
    #     max_cloud_cover=20.0,
    # )


if __name__ == "__main__":
    main()
