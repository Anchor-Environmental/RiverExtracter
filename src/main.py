from config_creator import main as create_config
from image_downloader import main as download_images
from image_lister_offline import main as list_offline_images
from image_lister_online import main as list_online_images
from image_processor import main as process_images


def main() -> None:
    bbox = (31.1482, -29.5482, 31.2075, -29.5882)
    start_date = "2024-05-01"
    end_date = "2024-05-30"
    config = create_config()

    online_acquisitions = list_online_images(
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        max_cloud_cover=20.0,
        config=config,
    )

    # offline_acquisitions = list_offline_images("./output")
    # print(offline_acquisitions)
    for val in online_acquisitions:
        print(val["properties"])
        # print(offline_acquisitions)
        path = download_images(
            bbox=bbox,
            start_date=val["properties"]["datetime"],
            end_date=val["properties"]["datetime"],
            config=config,
        )
        process_images(
            input_file_path=path,
            output_dir="output",
            threshold=0.0,
        )


if __name__ == "__main__":
    main()
