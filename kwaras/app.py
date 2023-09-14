#! env python3

import argparse
import os.path
# import traceback
import json
from gooey import Gooey
from typing import Optional, Sequence
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
    from kwaras.conf import config
    from kwaras.formats.lift import Lift
    from kwaras.process import liftadd

    # TODO: change ConfigWindow to subparser
    config.ConfigWindow("lexicon.cfg", parts=["EAFL"])

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

@Gooey
def main(argv: Optional[Sequence[str]] = None):
    argv = parse_args()

    if argv.convert_lexicon:
        convert_lexicon()

    if argv.export_corpus:
        export_corpus(argv.config)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--convert-lexicon", action="store_true",
                        help="Convert FLEx LIFT lexicon to ELAN-Corpa EAFL lexicon")
    parser.add_argument("--export-corpus", action="store_true",
                        help="Export an ELAN corpus as web interface files")
    parser.add_argument("--select-action", action="store_true",
                        help="Use GUI widget to choose action")
    parser.add_argument("--config",
                        help="Path of the config file to read")

    return parser.parse_args()


# class ChoiceWindow:
#     def __init__(self, args):
#         self.args = args
#         self.tkroot = tk.Tk()
#         self.tkroot.title("Choose Process")

#         # Make container frame
#         self.frame = tk.Frame(self.tkroot, relief=RIDGE, borderwidth=2)
#         self.frame.grid(column=0, row=0, sticky=(N, W, E, S))
#         self.frame.columnconfigure(0, weight=1)
#         self.frame.rowconfigure(0, weight=1)
#         self.frame.pack(fill=BOTH, expand=1)

#         label = tk.Label(self.frame, text="Process")
#         label.grid(row=10, column=1, sticky=E)
#         self.var = tk.StringVar()
#         entry = tk.OptionMenu(self.frame, self.var, "Export Corpus", "Convert Lexicon")
#         entry.grid(row=10, column=2, sticky=W)

#         button = tk.Button(self.frame, text="Okay", command=self._destroy_root)
#         button.grid(row=100, column=3, sticky=E)
#         tk.mainloop()

#     def _destroy_root(self):
#         self.tkroot.destroy()
#         var_str = self.var.get()
#         if var_str == "Export Corpus":
#             self.args.export_corpus = True
#         elif var_str == "Convert Lexicon":
#             self.args.convert_lexicon = True
#         else:
#             tkinter.messagebox.showerror("Unrecognized process name")


if __name__ == "__main__":
    # args = parse_args()
    # if args.select_action:
    #     ChoiceWindow(args)
    # elif not (args.convert_lexicon or args.export_corpus):
    #     args.export_corpus = True
    main()
