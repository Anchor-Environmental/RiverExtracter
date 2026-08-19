# River Extractor

River Extractor functions as a Python CLI tool and library
for downloading imagery from Sentinel Hub and extracting surface water 
using NDWI (Normalized Difference Water Index)
  
---
## Requirements 

- Python 3.10 or newer
- Copernicus Data Space credentials for downloading imagery
- GeoTIFF input containing Green and NIR bands when processing local imagery

## Credential management

- make an account or login at https://dataspace.copernicus.eu
- go to sentinel hub dashboard
- go to user settings and create a new OAuth client
- add the Client_ID and Client_Secret to CDSE_CLIENT_ID and CDSE_CLIENT_SECRET in your system environment variables

To temporarily save credentials:

```bash
export CDSE_CLIENT_ID="your-client-id"
export CDSE_CLIENT_SECRET="your-client-secret"
```

To persist credentials on Unix type systems add them to ~/.zshrc on mac or 

To persist credentials on Windows search for env in the start menu. Go to environment variables, click new by system variables and add CDSE_CLIENT_ID and CDSE_CLIENT_SECRET

## Installation from GitHub

```bash
python -m pip install "https://github.com/Anchor-Environmental/RiverExtracter.git"
```

# Development installation

Clone the repository:

```bash
git clone https://github.com/Anchor-Environmental/RiverExtracter.git
cd RiverExtracter
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install package and dependencies:

```bash
python -m pip install --upgrate pip
python -m pip install -e ".[dev]"
```

# Confirm installation

Display avaliable options: 

```bash
river-extractor --help
```



---
