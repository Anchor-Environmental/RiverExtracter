from config import CDSE_CLIENT_ID, CDSE_CLIENT_SECRET


def create_config(client_id, client_secret, token_url, base_url) -> SHConfig:
    TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    BASE_URL = "https://sh.dataspace.copernicus.eu"
    """
    Reads credentials from environment variables.
    Required:
        CDSE_CLIENT_ID
        CDSE_CLIENT_SECRET
    """
    config = SHconfig()
    client_id = CDSE_CLIENT_ID
    client_secret = CDSE_CLIENT_SECRET

    config.sh_client_id = client_id
    config.sh_client_secret = client_secret
    config.sh_base_url = BASE_URL
    config.sh_token_url = TOKEN_URL

    config.save("cdse_temp")

    return SHConfig("cdse_temp")


def main() -> SHConfig:
    
