from config import BASE_URL, CDSE_CLIENT_ID, CDSE_CLIENT_SECRET, TOKEN_URL
from sentinelhub import SHConfig


def create_config(client_id, client_secret, token_url, base_url) -> SHConfig:
    """
    Reads credentials from environment variables.
    Required:
        CDSE_CLIENT_ID
        CDSE_CLIENT_SECRET
    """
    config = SHConfig()

    config.sh_client_id = client_id
    config.sh_client_secret = client_secret
    config.sh_base_url = base_url
    config.sh_token_url = token_url

    config.save("cdse_temp")

    return SHConfig("cdse_temp")


def main() -> SHConfig:
    return create_config(CDSE_CLIENT_ID, CDSE_CLIENT_SECRET, TOKEN_URL, BASE_URL)
