import os

from sentinelhub import SHConfig

DEFAULT_BASE_URL = "https://sh.dataspace.copernicus.eu"
DEFAULT_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"


def create_config(
    client_id: str | None = None,
    client_secret: str | None = None,
    token_url: str = DEFAULT_TOKEN_URL,
    base_url: str = DEFAULT_BASE_URL,
) -> SHConfig:
    """
    Creates a Sentinel hub config compatible with Copernicus Data Space

    Create environment vairables for CDSE_CLIENT_ID and CDSE_CLIENT_SECRET or pass them directly

    Parameters:
        client_id:
            If this is not provided then it is read from the environment variables

        client_secret:
            If this is not provided then it is read from the environement variables

        token_url:
            OAuth token endpoint

        base_url:
            Sentinel hub service endpoint

    Returns:
        sentinelhub.SHConfig

    Raises:
        RuntimeError:
            If the client_id or client_secret is unavaliable
    """

    resolved_client_id = client_id or os.environ.get("CDSE_CLIENT_ID")
    resolved_client_secret = client_secret or os.environ.get("CDSE_CLIENT_SECRET")

    missing_variables = []

    if not resolved_client_id:
        missing_variables.append("CDSE_CLIENT_ID")

    if not resolved_client_secret:
        missing_variables.append("CDSE_CLIENT_SECRET")

    if missing_variables:
        missing_names = ", ".join(missing_variables)

        raise RuntimeError(
            f"Missing Copernicus Marine Data Space credentials: {missing_names}"
            "Please remember to set the enviroment variables for CDSE_CLIENT_SECRET and CDSE_CLIENT_ID"
        )

    config = SHConfig()

    config.sh_client_id = resolved_client_id
    config.sh_client_secret = resolved_client_secret
    config.sh_base_url = base_url
    config.sh_token_url = token_url

    return config
