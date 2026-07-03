from pathlib import Path

from mca_model.model.model import Model
from mca_model.plumbing import build

ROOT = Path(__file__).parent


def load_model(i:int=0) -> Model:
    return build.load(ROOT/f'model{i:02}.toml')


MODEL0 = load_model(0)
ASSET0 = MODEL0.list_assets()[0]

              

