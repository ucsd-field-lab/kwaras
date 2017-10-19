# -*- coding: utf-8 -*-
"""
Created on Sept 24, 2016

@author: lucien
"""

import os
import json

from ..formats import eaf, utfcsv


def main():
    cfg_file = "config.txt"
    up_dir = os.path.dirname(os.getcwd())
    cfg = json.load(os.path.join(up_dir, cfg_file))
    csvfile = utfcsv.UnicodeWriter(os.path.join(cfg["FILE_DIR"], "status.csv"), "excel", mode="ab")
    csvfile.write(["Filename"] + cfg["EXPORT_FIELDS"])

    for filename in os.listdir(os.path.join(cfg["FILE_DIR"], cfg["OLD_EAFS"])):
        print filename
        if not os.path.splitext(filename)[1].lower() == ".eaf":
            print "Not an eaf:", filename, os.path.splitext(filename)
        else:
            fpath = os.path.join(cfg["FILE_DIR"], cfg["OLD_EAFS"], filename)
            template = os.path.join(cfg["FILE_DIR"], cfg["TEMPLATE"])
            eafile = clean_eaf(fpath, template)
            eafile.write(os.path.join(cfg["FILE_DIR"], cfg["NEW_EAFS"], filename))
            eafile.export_to_csv(os.path.join(cfg["FILE_DIR"], cfg["CSV"]), "excel", cfg["EXPORT_FIELDS"], "ab")
            status = sorted(eafile.status(cfg["EXPORT_FIELDS"]).items())
            print status
            csvfile.write([filename] + [str(v * 100) + "%" for (k, v) in status])


def clean_eaf(fname, template=None):
    eafile = eaf.Eaf(fname)

    if template is not None:
        eafile.import_types(template)

    tids = eafile.get_tier_ids()
    spkrs = set([s.partition('@')[2] for s in tids])

    for s in spkrs:
        clean_eaf_block(eafile, s)

    return eafile


def clean_eaf_block(eafile, spkr=''):
    pass


if __name__ == "__main__":
    main()
