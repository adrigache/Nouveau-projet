import tomli_w
from pathlib import Path

from mca_model.config import rc
from mca_model.repository.filesystem import read_xls
from mca_model.plumbing import build




# def dump_to_yaml(data:dict, fname:Path):
#     """"""
#     with file(fname, 'w') as f:
#         yaml.dump(data, f)

        
def dump_to_toml(data:dict, fname:Path):
    """"""
    with open(fname, "wb") as f:
        tomli_w.dump(data, f)



def load_model(fname:Path, **kwargs):
    """"""
    if fname.suffix == '.toml':
        return build.load(fname, **kwargs)
    if fname.suffix in ['.xlsx', '.xls']:
        try:
            model_as_dict = read_xls.load_model(fname, **kwargs)
            return build.make_model(model_as_dict, **kwargs)
        except KeyError:
            rc.fail('file is not tagged, will try automatic tagging')
            return actions.tag(fname, **kwargs)


    raise ValueError(f"Unsupported file suffix: {fname.suffix}")



from mca_model.service import actions
