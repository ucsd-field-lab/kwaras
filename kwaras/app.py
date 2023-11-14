#! env python3

import argparse
import os
# import traceback
import json
from pathlib import Path
from typing import Optional, Sequence, Union
from kwaras.conf.config import init_config_parser, init_eafl_parser, init_csv_parser, init_html_parser, add_language_arg, _open_cfg_safe

import importlib
# import tkinter as tk
# import tkinter.messagebox
# from tkinter.constants import *

# try:
#     import kwaras
# except ImportError as e:

#     tkinter.messagebox.showerror(title="Package not installed.",
#                            message="The 'kwaras' package has not been installed correctly yet. "
#                                    "Run installer before running this.")
#     raise e

GOOEY = importlib.util.find_spec('gooey_tools') is not None

if not GOOEY:
    # hacky way of avoiding calling gooey_tools
    # TODO: clean this up
    def innocent_wrapper(f=None, **_):
        if not callable(f):
            return lambda f: innocent_wrapper(f)
        return f
    HybridGooey = innocent_wrapper
    HybridGooeyParser = argparse.ArgumentParser
    def add_arg_nogui(parser, *args, **kwargs):
        kwargs.pop('widget', None)
        if kwargs.get('action', None) in ('store_true', 'store_false'):
            kwargs.pop('metavar', None)
        return parser.add_argument(*args, **kwargs)
    add_hybrid_arg = add_arg_nogui
else:
    from gooey_tools import HybridGooey, HybridGooeyParser, add_hybrid_arg

def convert_lexicon(eafl_cfg):
    from kwaras.formats.lift import Lift
    from kwaras.process import liftadd


    dir_name = eafl_cfg["EAFL_DIR"]
    inf_name = eafl_cfg["LIFT"]

    base, ext = os.path.splitext(inf_name)

    if ext != '.lift':
        raise RuntimeError('LIFT file in lexicon.cfg does not have .lift extension.')

    print("Exposing GUID as field in", inf_name)
    # update GUID field in lexicon
    lift = Lift(inf_name)
    lift = liftadd.exposeGuid(lift)
    lift.write(os.path.join(dir_name, base + "-guid.lift"))

    # add allomorphs to LIFT file
    print("Adding allomorphs to", inf_name)
    lift = liftadd.addRarAllomorphs(lift)
    # dump the LIFT data to a new file
    outf_name = os.path.join(dir_name, base + "-added.lift")
    lift.write(outf_name)
    print("Data written to", outf_name)

    print("Converting LIFT format to EAFL format")
    eafl_name = os.path.join(dir_name, base + "-import.eafl")
    lift.toEAFL(eafl_name)
    print("Data written to", eafl_name)


def export_corpus(web_cfg):
    from kwaras.conf import config
    from kwaras.process import web

    web.main(web_cfg)


def make_config(cfg_obj: dict, fp: Union[os.PathLike, str]) -> str:
    """
    JSONifies config args object
    """
    # TODO: validate cfg_obj
    with open(fp, 'w') as f:
        json.dump(cfg_obj, f, indent=4)
    return fp
    

@HybridGooey
def main(argv: Optional[Sequence[str]] = None):
    cwd_files = os.listdir('.')
    cfg = None
    for fp in cwd_files:
        if Path(fp).suffix == '.cfg':
            cfg = fp
            break
    argv = parse_args(argv, cfg)

    # reset cfg to None
    # check if config arg was passed
    # if not, use arg values passed by user
    cfg = None
    if argv.config:
        cfg = argv.config
        with open(cfg) as f:
            cfg = json.load(f)

    if argv.command == 'convert-lexicon':
        if not cfg:
            cfg = vars(argv)
        convert_lexicon(cfg)

    if argv.command == 'export-corpus':
        if not cfg:
            cfg = vars(argv)
        export_corpus(cfg)

    if argv.command == 'make-config':
        args = vars(argv)
        cfg_file = args.pop('CFG_FILE')
        args.pop('command')
        args.pop('config')
        make_config(args, cfg_file)


def parse_args(
        argv: Optional[Sequence[str]] = None,
        cfg_file: Union[str, os.PathLike, None] = None,
    ) -> argparse.Namespace:
    cfg = _open_cfg_safe(cfg_file)
    parser = HybridGooeyParser()
    subparsers = parser.add_subparsers(dest='command')

    lexicon_parser = subparsers.add_parser("convert-lexicon",
                        help="Convert FLEx LIFT lexicon to ELAN-Corpa EAFL lexicon")
    eafl_group = init_eafl_parser(lexicon_parser, cfg)
    add_language_arg(eafl_group, cfg.get('LANGUAGE', None))
    corpus_parser = subparsers.add_parser("export-corpus",
                        help="Export an ELAN corpus as web interface files")
    csv_group = init_csv_parser(corpus_parser, cfg)
    init_html_parser(corpus_parser, cfg)
    add_language_arg(csv_group, cfg.get('LANGUAGE', None))
    config_parser = subparsers.add_parser("make-config",
                        help="Create language.cfg file for a kwaras project.")
    init_config_parser(config_parser, cfg_file)
    # parser.add_argument("--select-action", action="store_true",
    #                     help="Use GUI widget to choose action")
    parser.add_argument("--config",
                        help="Path of the config file to read")

    return parser.parse_args(argv)



if __name__ == "__main__":
    main()
