from sentinelhub import (
    CRS,
    BBox,
    DataCollection,
    MimeType,
    MosaickingOrder,
    SentinelHubCatalog,
    SentinelHubRequest,
    SHConfig,
    bbox_to_dimensions,
)

from config import CDSE_CLIENT_ID, CDSE_CLIENT_SECRET


def get_available_acquisitions(bbox, start_date, end_date, max_cloud_cover, config):

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


# ------------------------------------------------------------------
# Copernicus Data Space configuration
# ------------------------------------------------------------------


def get_config() -> SHConfig:
    TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    BASE_URL = "https://sh.dataspace.copernicus.eu"
    """
    Reads credentials from environment variables.
    Required:
        CDSE_CLIENT_ID
        CDSE_CLIENT_SECRET
    """
    config = SHConfig()
    client_id = CDSE_CLIENT_ID
    client_secret = CDSE_CLIENT_SECRET

    config.sh_client_id = client_id
    config.sh_client_secret = client_secret
    config.sh_base_url = BASE_URL
    config.sh_token_url = TOKEN_URL

    config.save("cdse_temp")

    return SHConfig("cdse_temp")


def main(bbox, start_date, end_date, max_cloud_cover):

    config = get_config()
    bbox_obj = BBox(bbox=bbox, crs=CRS.WGS84)

    acquisitions = get_available_acquisitions(
        bbox=bbox_obj,
        start_date=start_date,
        end_date=end_date,
        max_cloud_cover=max_cloud_cover,
        config=config,
    )

    for item in acquisitions:
        print(item["properties"]["datetime"])
