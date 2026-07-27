import requests
import os
from config import CDSE_CLIENT_ID, CDSE_CLIENT_SECRET
client_id = CDSE_CLIENT_ID
client_secret = CDSE_CLIENT_SECRET
url = (
    "https://identity.dataspace.copernicus.eu/"
    "auth/realms/CDSE/protocol/openid-connect/token"
)
response = requests.post(
    url,
    data={
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    },
)
print(response.status_code)
print(response.text)