#!/usr/bin/env python
import argparse
from pathlib import Path

from typing import List


from mca_model.config import rc
from mca_model.service import actions





def action_explore(args):
    """"""
    explored = actions.exploring(args.filename, args.debug)

    return explored


def action_tag(args):
    """"""
    tagged = actions.tag(args.filename, args.debug)
    print(tagged)

    tagged.dump()
    return tagged


def action_compute(args):
    """"""
    model, by_assets = actions.compute(args.filename, args.debug)
    agg = actions.aggregate(model, by_assets)
    return model, by_assets, agg

        
def main(args):
    """"""
    rc.header('main', f'action: `{args.action}`')

    assert(args.filename.exists())
    
    match args.action:
        case 'tag':
            return True, action_tag(args)
        
        case 'compute':
            return True, action_compute(args)

        case 'explore':
            return True, action_explore(args)
        
        case _:
            rc.p(f"action '{tag}': nothing to do")
            pass
        # case 'raw':
        #     actions.explore_raw()

    return False, None

        
def parse_args(args:List[str]|None=None):
    """"""
    # common part
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('filename', type=Path)
    common.add_argument('--debug', action='store_true')
    
    # subparser
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='action', required=True)
    
    sub.add_parser('tag', parents=[common])
    sub.add_parser('compute', parents=[common])
    sub.add_parser('explore', parents=[common])
    # sub.add_parser('results', parents=[common])

    # done
    return parser.parse_args(args)

    
if __name__ == '__main__':
    args = parse_args()
    main(args)
    
