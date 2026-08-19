from pathlib import Path


def list_offline_images(
    directory: str | Path,
) -> list:
    """
    Return filenames of downloaded images in the downloads folder

    Parameters:

    directory:
        Where to look for the files

    recursive:
        If true then this will search subdirectories

    Returns list[str]:
        Stored list of GeoTIFF image filenames

    Raises:
        FileNotFoundError
            If the files does not exist

        NotADirectoryError
            If the directory is not a directory


    """
    directory = Path(directory)

    if not directory.exists():
        raise FileNotFoundError(f"File does not exist: {directory}")

    if not directory.is_dir():
        raise NotADirectoryError(f"Acquisition path is not a directory: {directory}")

    return sorted(path.name for path in directory.glob("*.tif") if path.is_file())
