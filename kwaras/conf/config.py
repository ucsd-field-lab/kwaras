
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
        "LANGUAGE",
        metavar="Language configuration:",
        default=lang
    )

    add_hybrid_arg(
        config_parser,
        "CFG_PATH",
        metavar="Path to save config to:",
        default=cfg_file,
        type='file'
    )

    eafl = config_parser.add_argument_group('eafl')
    add_hybrid_arg(
        eafl,
        "LIFT",
        metavar="Input LIFT file:",
        type='file',
        default=cfg.get("LIFT", os.path.join(updir, "FLEx.lift")),
    )
    add_hybrid_arg(
        eafl,
        "EAFL_DIR",
        metavar="Output EAFL Directory:",
        type='dir',
        default=cfg.get("EAFL_DIR", updir),
    )

    csv = config_parser.add_argument_group('csv')
    init_dir = cfg.get("FILE_DIR", updir)
    add_hybrid_arg(
        csv,
        "FILE_DIR",
        metavar="Working File Directory:",
        type='dir',
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
        "EXP_FIELDS",
        default=exp_fields,
        help="List of Fields to Export",
        nargs='+'
    )

    init_eafs = cfg.get("OLD_EAFS", old_eafs)
    add_hybrid_arg(
        csv,
        "OLD_EAFS",
        metavar="Directory of Input EAFs:",
        type='dir',
        default=init_eafs,
    )
    # self.mk_choice_row("NEW_EAFS", os.path.join(init_eafs, "auto"), "Directory for Output EAFs:", isdir=True)

    html = config_parser.add_argument_group('html')
    init_meta = cfg.get("META", os.path.join(updir, "metadata.csv"))
    add_hybrid_arg(
        html,
        "META",
        metavar="WAV Session Metadata (optional):",
        type='file',
        default=init_meta,
    )
    init_wav = cfg.get("WAV", os.path.join(updir, "wav"))
    add_hybrid_arg(
        html,
        "WAV",
        metavar="WAV Input Directory:",
        type='dir',
        default=init_wav,
    )
    init_www = cfg.get("WWW", os.path.join(updir, "www"))
    add_hybrid_arg(
        html,
        "WWW",
        metavar="Web Files Output Directory:",
        type='dir',
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
        "NAV_BAR",
        metavar="HTML div for Navigation",
        default=nav_bar,
    )

# class ConfigWindow:
#     def __init__(self, cfg_file=CFG_FILE, parts=("EAFL", "CSV", "HTML"), defaults=None):
#         self.tkroot = tk.Tk()
#         self.tkroot.title("Configuration Settings")

#         self.cfg_file = cfg_file
#         self.labels = {}
#         self.entries = {}
#         self.variables = {}
#         self.buttons = {}
#         self.indices = []
#         if defaults is None:
#             defaults = {}

#         # Make container frame
#         self.frame = tk.Frame(self.tkroot, relief=RIDGE, borderwidth=2)
#         self.frame.grid(column=0, row=0, sticky=(N, W, E, S))
#         self.frame.columnconfigure(0, weight=1)
#         self.frame.rowconfigure(0, weight=1)
#         self.frame.pack(fill=BOTH, expand=1)

#         # Load previous configuration settings
#         if os.path.exists(cfg_file):
#             cfgstr = ''.join(list(open(cfg_file)))
#             if cfgstr:
#                 self.cfg = json.loads(cfgstr)
#             else:
#                 self.cfg = {}
#         else:
#             self.cfg = {}

#         self.tkroot.protocol("WM_DELETE_WINDOW", self._destroy_root)
#         self.tkroot.protocol("<DESTROY>", self._destroy_root)

#         updir = os.path.dirname(os.getcwd())
#         old_eafs = os.path.join(updir, "corpus-data-versions")

#         if "MAIN" in parts:
#             self.mk_menu_row("LANGUAGE", defaults.get("LANGUAGE", cfg_file.split('.')[0]), "Language template:")

#         if "EAFL" in parts:
#             self.mk_label_row("Variables used in creating EAFL file")
#             init_lift = self.cfg.get("LIFT", os.path.join(updir, "FLEx.lift"))
#             self.mk_choice_row("LIFT", init_lift, "Input LIFT File:")
#             init_dir = self.cfg.get("EAFL_DIR", updir)
#             self.mk_choice_row("EAFL_DIR", init_dir, "Output EAFL Directory:", isdir=True)

#         if "CSV" in parts or "HTML" in parts:
#             self.mk_label_row("Variables used in both CSV and HTML export steps")
#             init_dir = self.cfg.get("FILE_DIR", updir)
#             self.mk_choice_row("FILE_DIR", init_dir, "Working File Directory:", isdir=True)
#             out_dir = os.path.join(old_eafs, "auto")
#             if not os.path.exists(out_dir):
#                 out_dir = init_dir
#             # init_csv = self.cfg.get("CSV", os.path.join(out_dir, "data.csv"))
#             # self.mk_choice_row("CSV", init_csv, "Output CSV File:", issave=True)

#             exp_fields = self.cfg.get("EXP_FIELDS",  # List of fields to include
#                                       ", ".join(["Phonetic", "Spanish", "English", "Note"]))
#             self.mk_text_row("EXP_FIELDS", exp_fields, "List of Fields to Export:")

#             init_eafs = self.cfg.get("OLD_EAFS", old_eafs)
#             self.mk_choice_row("OLD_EAFS", init_eafs, "Directory of Input EAFs:", isdir=True)
#             # self.mk_choice_row("NEW_EAFS", os.path.join(init_eafs, "auto"), "Directory for Output EAFs:", isdir=True)

#         if "HTML" in parts:
#             self.mk_label_row("Variables used for exporting CSV to HTML")
#             init_meta = self.cfg.get("META", os.path.join(updir, "metadata.csv"))
#             self.mk_choice_row("META", init_meta, "WAV Session Metadata (optional):")
#             init_wav = self.cfg.get("WAV", os.path.join(updir, "wav"))
#             self.mk_choice_row("WAV", init_wav, "WAV Input Directory:", isdir=True)
#             init_www = self.cfg.get("WWW", os.path.join(updir, "www"))
#             self.mk_choice_row("WWW", init_www, "Web Files Output Directory:", isdir=True)
#             # init_clips = self.cfg.get("CLIPS", os.path.join(updir, "audio", "www", "clips"))
#             # self.mk_choice_row("CLIPS", init_clips, "WAV Clips Output Directory:", isdir=True)

#             self.mk_text_row("PG_TITLE", "Kwaras Corpus", "HTML Page Title:")
#             nav_bar = """<div align="right">
#                 <a href="index.html">Corpus</a>
#                 - <a href="dict.xhtml">Dictionary</a>
#                 </div>"""
#             nav_bar = self.cfg.get("NAV_BAR", nav_bar)
#             self.mk_text_box("NAV_BAR", nav_bar, "HTML div for Navigation", rowspan=4)

#         self.buttons["Okay"] = tk.Button(self.frame, text="Okay", command=self._destroy_root)
#         self.buttons["Okay"].grid(row=100, column=3, sticky=E)

#         self._focus()
#         self.tkroot.mainloop()

#     def _focus(self):
#         self.tkroot.attributes("-topmost", True)
#         if sys.platform == "darwin":
#             # MacOS doesn't let tk manipulate window order, so use an applescript command
#             command = """ /usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' """
#             try:
#                 subprocess.check_call(shlex.split(command))
#             except subprocess.CalledProcessError as e:
#                 print("Warning: Unable to bring Kwaras window to front.")
#                 print((e.message))
#         self.tkroot.focus_force()
#         self.tkroot.attributes("-topmost", False)

#     def _destroy_root(self):
#         """Store config settings on close"""
#         self.tkroot.destroy()
#         for varname in self.variables:
#             self.cfg[varname] = self.variables[varname].get()
#             # print "Setting", varname, self.variables[varname].get()
#         # print "Writing settings to", self.cfg_file
#         with open(self.cfg_file, "w") as cfg_fs:
#             json.dump(self.cfg, cfg_fs, indent=3, separators=(',', ': '))

#     def _insert_index(self, idx):
#         self.indices += [idx]
#         self.indices.sort()

#     def mk_label_row(self, text, idx=-1):
#         """Make Subheading Labels"""
#         idx = idx if idx > 0 and idx not in self.indices else max(self.indices + [0]) + 1
#         self._insert_index(idx)
#         tk.Label(self.frame, text=text,
#                  font=("Helvetica", 12)).grid(row=idx, column=1, columnspan=3, sticky=(E, W))

#     def mk_text_row(self, var, default, text, idx=-1):
#         """Make single-line Entry row"""
#         idx = idx if idx > 0 and idx not in self.indices else max(self.indices + [0]) + 1
#         self._insert_index(idx)
#         self.labels[var] = tk.Label(self.frame, text=text)
#         self.labels[var].grid(row=idx, column=1, sticky=E)
#         self.variables[var] = tk.StringVar(value=self.cfg.get(var, default))
#         self.entries[var] = tk.Entry(self.frame, textvariable=self.variables[var], width=_WIDTH)
#         self.entries[var].grid(row=idx, column=2, sticky=W)

#     def mk_text_box(self, var, default, text, rowspan=2, idx=-1):
#         """Make a multi-line Text Box field"""
#         idx = idx if idx > 0 and idx not in self.indices else max(self.indices + [0]) + 1
#         self._insert_index(idx)
#         self.labels[var] = tk.Label(self.frame, text=text)
#         self.labels[var].grid(row=idx, column=1, sticky=E)
#         self.variables[var] = tk.StringVar(value=self.cfg.get(var, default))
#         self.entries[var] = MyText(self.frame, self.variables[var], width=_WIDTH, height=rowspan,
#                                    font=("Helvetica", 12))
#         self.entries[var].grid(row=idx, column=2, columnspan=1, sticky=W)

#     def mk_menu_row(self, var, default, text, idx=-1):
#         """Make Option Menu rows"""
#         idx = idx if idx > 0 and idx not in self.indices else max(self.indices + [0]) + 1
#         self._insert_index(idx)
#         self.labels[var] = tk.Label(self.frame, text=text)
#         self.labels[var].grid(row=idx, column=1, sticky=E)
#         self.variables[var] = tk.StringVar(value=self.cfg.get(var, default))
#         self.entries[var] = tk.OptionMenu(self.frame, self.variables[var], "Raramuri", "Kumiai", "Mixtec", "Other")
#         self.entries[var].grid(row=idx, column=2, sticky=W)

#     def mk_choice_row(self, var, default, text, isdir=False, issave=False, idx=-1):
#         """Make a row for a File/Directory selector"""
#         idx = idx if idx > 0 and idx not in self.indices else max(self.indices + [0]) + 1
#         self._insert_index(idx)
#         self.labels[var] = tk.Label(self.frame, text=text)
#         self.labels[var].grid(row=idx, column=1, sticky=E)
#         self.variables[var] = tk.StringVar(value=self.cfg.get(var, default))
#         self.entries[var] = tk.Entry(self.frame, textvariable=self.variables[var], width=_WIDTH)
#         self.entries[var].grid(row=idx, column=2, sticky=W)

#         def callback():
#             options = {
#                 'initialdir': self.variables[var].get(),
#                 'parent': self.tkroot,
#                 'title': "Choose " + text
#             }
#             if not os.path.exists(options['initialdir']):
#                 options['initialdir'] = ''
#             if isdir:
#                 dvar = tkinter.filedialog.askdirectory(**options)
#             elif issave:
#                 dvar = tkinter.filedialog.asksaveasfilename(**options)
#             else:
#                 dvar = tkinter.filedialog.askopenfilename(**options)
#             self.variables[var].set(dvar)

#         self.buttons[var] = tk.Button(self.frame, text="Choose", command=callback)
#         self.buttons[var].grid(row=idx, column=3, sticky=E)


# # Text Entry Boxes
# class MyText(tk.Text):
#     def __init__(self, master=None, textvar=None, *options, **kw):
#         tk.Text.__init__(self, master, *options, **kw)
#         if textvar is not None:
#             self.textvar = textvar
#         else:
#             self.textvar = tk.StringVar()
#         self.insert("1.0", self.textvar.get())

#     def destroy(self):
#         self.textvar.set(self.get("1.0", END))
#         tk.Text.destroy(self)


# if __name__ == "__main__":
#     ConfigWindow(CFG_FILE)
