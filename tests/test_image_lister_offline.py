from river_extractor.image_lister_offline import list_offline_images


def test_list_offline_images_returns_sorted_tiffs(tmp_path):
    (tmp_path / "sentinel_image_2022-04-30.tif").touch()
    (tmp_path / "sentinel_image_2022-04-20.tif").touch()
    (tmp_path / "notes.txt").touch()

    result = list_offline_images(tmp_path)

    assert result == [
        "sentinel_image_2022-04-20.tif",
        "sentinel_image_2022-04-30.tif",
    ]


def test_list_offline_images_empty_directory(tmp_path):
    assert list_offline_images(tmp_path) == []
