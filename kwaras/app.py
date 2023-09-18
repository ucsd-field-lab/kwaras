#! env python3

import argparse
import os
# import traceback
import json
from gooey_tools import HybridGooey, HybridGooeyParser
from pathlib import Path
from typing import Optional, Sequence, Union
from kwaras.conf.config import init_config_parser
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


def convert_lexicon():
    from kwaras.formats.lift import Lift
    from kwaras.process import liftadd

    cfg = json.load(open("lexicon.cfg"))
    dir_name = cfg["EAFL_DIR"]
    inf_name = cfg["LIFT"]

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


def export_corpus(cfg_path):
    from kwaras.conf import config
    from kwaras.process import web

    if not cfg_path:
        window = config.ConfigWindow("corpus.cfg", parts=["MAIN"])

        main_cfg = json.load(open("corpus.cfg"))
        cfg_path = "{0}.cfg".format(main_cfg["LANGUAGE"])

    window = config.ConfigWindow(cfg_path, parts=["MAIN", "CSV", "HTML"])

    cfg = json.load(open(cfg_path))
    web.main(cfg)

def make_config(cfg_obj: dict, fp: Union[os.PathLike, str]) -> str:
    """
    JSONifies config args object
    """
    # TODO: validate cfg_obj
    with open(fp, 'w') as f:
        json.dump(cfg_obj, f)
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

    if argv.command == 'convert-lexicon':
        convert_lexicon()

    if argv.command == 'export-corpus':
        export_corpus(argv.config)

    if argv.command == 'make-config':
        args = vars(argv)
        cfg_file = args.pop('CFG_FILE')
        make_config(args, cfg_file)


def parse_args(
        argv: Optional[Sequence[str]] = None,
        cfg: Union[str, os.PathLike, None] = None,
    ) -> argparse.Namespace:
    parser = HybridGooeyParser()
    subparsers = parser.add_subparsers(dest='command')

    lexicon_parser = subparsers.add_parser("convert-lexicon",
                        help="Convert FLEx LIFT lexicon to ELAN-Corpa EAFL lexicon")
    corpus_parser = subparsers.add_parser("export-corpus",
                        help="Export an ELAN corpus as web interface files")
    config_parser = subparsers.add_parser("make-config",
                        help="Create language.cfg file for a kwaras project.")
    init_config_parser(config_parser, cfg_file=cfg)
    # parser.add_argument("--select-action", action="store_true",
    #                     help="Use GUI widget to choose action")
    parser.add_argument("--config",
                        help="Path of the config file to read")

    return parser.parse_args(argv)



if __name__ == "__main__":
    main()
