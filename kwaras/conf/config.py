
import json
import os.path
from argparse import ArgumentParser
from typing import Sequence
from gooey_tools import add_hybrid_arg

CFG_FILE = "config.cfg"

def init_config_parser(
        config_parser: ArgumentParser,
        cfg_file: str = CFG_FILE,
        defaults: dict = dict(),
    ) -> None:
    updir = os.path.dirname(os.getcwd())
    old_eafs = os.path.join(updir, "corpus-data-versions")

    try:
        with open(cfg_file) as f:
            cfg = json.load(f)
    except FileNotFoundError:
        cfg = {}

    lang = defaults.get("LANGUAGE", cfg_file.split('.')[0])
    config_parser.add_argument(
        "--LANGUAGE",
        metavar="Language configuration:",
        default=lang
    )

    add_hybrid_arg(
        config_parser,
        "--CFG_FILE",
        metavar="Path to save config to:",
        default=cfg_file,
        type='filepath'
    )

    eafl = config_parser.add_argument_group('eafl')
    add_hybrid_arg(
        config_parser,
        "--LIFT",
        group=eafl,
        metavar="Input LIFT file:",
        type='filepath',
        default=cfg.get("LIFT", os.path.join(updir, "FLEx.lift")),
    )
    add_hybrid_arg(
        config_parser,
        "--EAFL_DIR",
        group=eafl,
        metavar="Output EAFL Directory:",
        type='dirpath',
        default=cfg.get("EAFL_DIR", updir),
    )

    csv = config_parser.add_argument_group('csv')
    init_dir = cfg.get("--FILE_DIR", updir)
    add_hybrid_arg(
        config_parser,
        "--FILE_DIR",
        group=csv,
        metavar="Working File Directory:",
        type='dirpath',
        default=init_dir,
    )
    out_dir = os.path.join(old_eafs, "auto")
    if not os.path.exists(out_dir):
        out_dir = init_dir
    # init_csv = self.cfg.get("CSV", os.path.join(out_dir, "data.csv"))
    # self.mk_choice_row("CSV", init_csv, "Output CSV File:", issave=True)

    exp_fields = cfg.get("EXP_FIELDS",  # List of fields to include
                                ", ".join(["Phonetic", "Spanish", "English", "Note"]))
    csv.add_argument(
        "--EXP_FIELDS",
        default=exp_fields,
        help="List of Fields to Export",
        nargs='+'
    )

    init_eafs = cfg.get("OLD_EAFS", old_eafs)
    add_hybrid_arg(
        config_parser,
        "--OLD_EAFS",
        group=csv,
        metavar="Directory of Input EAFs:",
        type='dirpath',
        default=init_eafs,
    )
    # self.mk_choice_row("NEW_EAFS", os.path.join(init_eafs, "auto"), "Directory for Output EAFs:", isdir=True)

    html = config_parser.add_argument_group('html')
    init_meta = cfg.get("META", os.path.join(updir, "metadata.csv"))
    add_hybrid_arg(
        config_parser,
        "--META",
        group=html,
        metavar="WAV Session Metadata (optional):",
        type='filepath',
        default=init_meta,
    )
    init_wav = cfg.get("WAV", os.path.join(updir, "wav"))
    add_hybrid_arg(
        config_parser,
        "--WAV",
        group=html,
        metavar="WAV Input Directory:",
        type='dirpath',
        default=init_wav,
    )
    init_www = cfg.get("WWW", os.path.join(updir, "www"))
    add_hybrid_arg(
        config_parser,
        "--WWW",
        group=html,
        metavar="Web Files Output Directory:",
        type='dirpath',
        default=init_www,
    )
    # init_clips = self.cfg.get("CLIPS", os.path.join(updir, "audio", "www", "clips"))
    # self.mk_choice_row("CLIPS", init_clips, "WAV Clips Output Directory:", isdir=True)

    #self.mk_text_row("PG_TITLE", "Kwaras Corpus", "HTML Page Title:")
    nav_bar = """<div align="right">
        <a href="index.html">Corpus</a>
        - <a href="dict.xhtml">Dictionary</a>
        </div>"""
    nav_bar = cfg.get("NAV_BAR", nav_bar)
    config_parser.add_argument(
        "--NAV_BAR",
        metavar="HTML div for Navigation",
        default=nav_bar,
    )
