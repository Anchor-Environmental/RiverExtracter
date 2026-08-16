from sentinelhub import CRS, BBox, DataCollection, SentinelHubCatalog


def get_available_acquisitions(
    bbox, start_date, end_date, max_cloud_cover, config
) -> list:

    catalog = SentinelHubCatalog(config=config)

    collection = DataCollection.SENTINEL2_L2A.define_from(
        "s212a_cdse", service_url=config.sh_base_url
    )

    search = catalog.search(
        collection=collection,
        bbox=bbox,
        time=(start_date, end_date),
        filter=f"eo:cloud_cover < {max_cloud_cover}",
    )
    return list(search)


def main(bbox, start_date, end_date, max_cloud_cover, config) -> list:

    bbox_obj = BBox(bbox=bbox, crs=CRS.WGS84)

    acquisitions = get_available_acquisitions(
        bbox=bbox_obj,
        start_date=start_date,
        end_date=end_date,
        max_cloud_cover=max_cloud_cover,
        config=config,
    )
    return acquisitions
