__author__ = 'Lucien'

import json
import os.path
import Tkinter as tk
import tkFileDialog
from Tkconstants import *

CFG_FILE = "config.txt"
_WIDTH = 60


class ConfigWindow:
    def __init__(self, cfg_file=CFG_FILE, parts=["EAFL", "CSV", "HTML"]):
        self.tkroot = tk.Tk()
        self.tkroot.title("Configuration Settings")

        self.cfg_file = cfg_file
        self.labels = {}
        self.entries = {}
        self.variables = {}
        self.buttons = {}
        self.indices = []

        # Make container frame
        self.frame = tk.Frame(self.tkroot, relief=RIDGE, borderwidth=2)
        self.frame.grid(column=0, row=0, sticky=(N, W, E, S))
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        self.frame.pack(fill=BOTH, expand=1)

        # Load previous configuration settings
        if os.path.exists(cfg_file):
            cfgstr = ''.join(list(open(cfg_file)))
            if cfgstr is not '':
                self.cfg = json.loads(cfgstr)
            else:
                self.cfg = {}
        else:
            self.cfg = {}

        self.tkroot.protocol("WM_DELETE_WINDOW", self._destroy_root)
        self.tkroot.protocol("<DESTROY>", self._destroy_root)

        updir = os.path.dirname(os.getcwd())
        old_eafs = os.path.join(updir, "corpus-data-versions")

        if "EAFL" in parts:
            self.mk_label_row("Variables used in creating EAFL file")
            init_lift = self.cfg.get("LIFT", os.path.join(updir, "FLEx.lift"))
            self.mk_choice_row("LIFT", init_lift, "Input LIFT File:")
            init_dir = self.cfg.get("EAFL_DIR", updir)
            self.mk_choice_row("EAFL_DIR", init_dir, "Output EAFL Directory:", isdir=True)

        if "CSV" in parts or "HTML" in parts:
            self.mk_label_row("Variables used in both CSV and HTML export steps")
            init_dir = self.cfg.get("FILE_DIR", updir)
            self.mk_choice_row("FILE_DIR", init_dir, "Working File Directory:", isdir=True)
            init_csv = self.cfg.get("CSV", os.path.join(old_eafs, "auto", "data.csv"))
            self.mk_choice_row("CSV", init_csv, "Output CSV File:")

            exp_fields = self.cfg.get("EXP_FIELDS",             # List of fields to include
                                      ["Broad", "Ortho", "NewOrtho", "Phonetic",
                                       "UttWGloss", "UttMGloss",
                                       "Spanish", "English", "Note"])
            self.mk_text_row("EXP_FIELDS", ", ".join(exp_fields), "List of Fields to Export:")

        if "CSV" in parts:
            self.mk_label_row("Variables used for exporting EAF to CSV")
            init_eafs = self.cfg.get("OLD_EAFS", old_eafs)
            self.mk_choice_row("OLD_EAFS", init_eafs, "Directory of Input EAFs:", isdir=True)
            self.mk_choice_row("NEW_EAFS", os.path.join(init_eafs, "auto"), "Directory for Output EAFs:", isdir=True)

        if "HTML" in parts:
            self.mk_label_row("Variables used for exporting CSV to HTML")
            init_meta = self.get("META", os.path.join(updir, "audio", "metadata.csv"))
            self.mk_choice_row("META", init_meta, "WAV Session Metadata:")
            init_wav = self.get("WAV", os.path.join(updir, "audio", "wav"))
            self.mk_choice_row("WAV", init_wav, "WAV Input Directory:", isdir=True)
            init_www = self.get("WWW", os.path.join(updir, "audio", "www"))
            self.mk_choice_row("WWW", init_www, "Web Files Output Directory:", isdir=True)
            init_clips = self.get("CLIPS", os.path.join(updir, "audio", "www", "clips"))
            self.mk_choice_row("CLIPS", init_clips, "WAV Clips Output Directory:", isdir=True)

            self.mk_text_row("PG_TITLE", "Kwaras Corpus", "HTML Page Title:")
            nav_bar = """<div align="right">
                <a href="index.html">Corpus</a> - <a href="dict.xhtml">Dictionary</a>
                </div>"""
            nav_bar = self.get("NAV_BAR", nav_bar)
            self.mk_text_box("NAV_BAR", nav_bar, "HTML div for Navigation", rowspan=4)

        self.buttons["Okay"] = tk.Button(self.frame, text="Okay", command=self._destroy_root)
        self.buttons["Okay"].grid(row=100, column=3, sticky=E)
        tk.mainloop()

    def _destroy_root(self):
        """Store config settings on close"""
        self.tkroot.destroy()
        for varname in self.variables:
            self.cfg[varname] = self.variables[varname].get()
            # print "Setting", varname, self.variables[varname].get()
        # print "Writing settings to", self.cfg_file
        with open(self.cfg_file, "w") as cfg_fs:
            json.dump(self.cfg, cfg_fs, indent=3, separators=(',', ': '))

    def _insert_index(self, idx):
        self.indices += [idx]
        self.indices.sort()

    def mk_label_row(self, text, idx=-1):
        """Make Subheading Labels"""
        idx = idx if idx > 0 and idx not in self.indices else max(self.indices + [0]) + 1
        self._insert_index(idx)
        tk.Label(self.frame, text=text,
                 font=("Helvetica", 12)).grid(row=idx, column=1, columnspan=3, sticky=(E, W))

    def mk_text_row(self, var, default, text, idx=-1):
        """Make Line Entry Rows"""
        idx = idx if idx > 0 and idx not in self.indices else max(self.indices + [0]) + 1
        self._insert_index(idx)
        self.labels[var] = tk.Label(self.frame, text=text)
        self.labels[var].grid(row=idx, column=1, sticky=E)
        self.variables[var] = tk.StringVar(value=self.cfg.get(var, default))
        self.entries[var] = tk.Entry(self.frame, textvariable=self.variables[var], width=_WIDTH)
        self.entries[var].grid(row=idx, column=2, sticky=W)

    def mk_text_box(self, var, default, text, rowspan=2, idx=-1):
        idx = idx if idx > 0 and idx not in self.indices else max(self.indices + [0]) + 1
        self._insert_index(idx)
        self.labels[var] = tk.Label(self.frame, text=text)
        self.labels[var].grid(row=idx, column=1, sticky=E)
        self.variables[var] = tk.StringVar(value=self.cfg.get(var, default))
        self.entries[var] = MyText(self.frame, self.variables[var], width=_WIDTH, height=rowspan, font=("Helvetica", 8))
        self.entries[var].grid(row=idx, column=2, columnspan=1, sticky=W)

    # File/Directory Choice UI Rows
    def mk_choice_row(self, var, default, text, isdir=False, idx=-1):
        idx = idx if idx > 0 and idx not in self.indices else max(self.indices + [0]) + 1
        self._insert_index(idx)
        self.labels[var] = tk.Label(self.frame, text=text)
        self.labels[var].grid(row=idx, column=1, sticky=E)
        self.variables[var] = tk.StringVar(value=self.cfg.get(var, default))
        self.entries[var] = tk.Entry(self.frame, textvariable=self.variables[var], width=_WIDTH)
        self.entries[var].grid(row=idx, column=2, sticky=W)

        def callback():
            options = {
                'initialdir': self.variables[var].get(),
                'parent': self.tkroot,
                'title': "Choose " + text
            }
            if isdir:
                dvar = tkFileDialog.askdirectory(**options)
            else:
                dvar = tkFileDialog.askopenfilename(**options)
            self.variables[var].set(dvar)

        self.buttons[var] = tk.Button(self.frame, text="Choose", command=callback)
        self.buttons[var].grid(row=idx, column=3, sticky=E)


# Text Entry Boxes
class MyText(tk.Text):
    def __init__(self, master=None, textvar=None, *options, **kw):
        tk.Text.__init__(self, master, *options, **kw)
        if textvar is not None:
            self.textvar = textvar
        else:
            self.textvar = tk.StringVar()
        self.insert("1.0", self.textvar.get())

    def destroy(self):
        self.textvar.set(self.get("1.0", END))
        tk.Text.destroy(self)

if __name__ == "__main__":
    ConfigWindow(CFG_FILE)
