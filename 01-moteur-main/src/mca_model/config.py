from pathlib import Path
from dotenv import load_dotenv
from os import getenv
import tomllib


# external lib
try:
    from rich_console import Console
except ModuleNotFoundError:
    raise Exception("Cannot load: `rich_console`")

rc = Console()
rc.header("config", "loading")

ROOT = Path(__file__).parents[2]
ENV = ROOT / ".env"

load_dotenv(ENV)



def get(s):
    my = getenv(s)
    if my is None:
        rc.header("config", f"missing entry: {s}", status=False, clear_previous=True)
        raise Exception(f"cannot find entry: {s}")
    return my


# path
PATH_ASSETS = ROOT / getenv("ASSETS", "assets")
FNAME_MODEL = PATH_ASSETS / get("FNAME_MODEL")

# TAGGING
FNAME_MODEL_TAG = Path(get("FNAME_MODEL_TAG"))

# - XLS
FNAME_MODEL_XLS = PATH_ASSETS / get("FNAME_MODEL_XLS")
MODEL_SHEETS = {
    "dashboard": "Dashboard",
    "model": "ass_Model",
    "vehicle": "ass_Vehicle",
    "market": "ass_Market",
    "asset": "ass_Asset",
    }

MODEL_SHEETS_COMPUTATIONS = {
    'overview':'Overview',
    'computations': 'Computations',
    'portfolio':'Portfolio'
    }


FOR_HUMANS = tomllib.load( open( ROOT/get('FOR_HUMANS'), 'rb'))

# 
ALLOW_UNITS_NUMBER = ['year', 'hours', 'kW', 'kWc', '€ / MWh', 'k€ / year']
ALLOW_UNITS_PRICE = ['€/MWh', 'k€/year']
XLS_DEFAULT_FIELD_NAME = 1
XLS_DEFAULT_OFFSET = 4
XLS_RIGHT_PANE_OFFSET = 11
XLS_MARKET_FIELD_NAME = 8  # colonne I, pour choper 'Market price scenario'


rc.header("config", "loaded", status=True, clear_previous=True)

# COLORS
BLUE="deep_sky_blue1"
RED='red'
GREY_LIGHT='grey93'
GREY='grey78'
YELLOW="khaki1"



