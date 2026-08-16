from pathlib import Path


def get_avaliable_acquisitions(path: str) -> list:

    os_path = Path(path)
    files = [f.name for f in os_path.rglob("*") if f.is_file()]

    return files


def main(path: str) -> list:
    acquisitions = get_avaliable_acquisitions(path)
    return acquisitions
