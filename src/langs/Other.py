# -*- coding: utf-8 -*-
"""
Created on Sept 24, 2016

@author: lucien
"""

import os
import re

from kwaras.formats import eaf, utfcsv


def main():

    csvfile = utfcsv.UnicodeWriter(os.path.join(cfg.FILE_DIR, "status.csv"), "excel", mode="ab")
    csvfile.write(["Filename"] + cfg.EXPORT_FIELDS)

    for filename in os.listdir(os.path.join(cfg.FILE_DIR, cfg.OLD_EAFS)):
        print filename
        if not os.path.splitext(filename)[1].lower() == ".eaf":
            print "Not an eaf:", filename, os.path.splitext(filename)
        else:
            fpath = os.path.join(cfg.FILE_DIR, cfg.OLD_EAFS, filename)
            template = os.path.join(cfg.FILE_DIR, cfg.TEMPLATE)
            eafile = cleanEaf(fpath, template)
            eafile.write(os.path.join(cfg.FILE_DIR, cfg._NEW_EAFS, filename))
            eafile.exportToCSV(os.path.join(cfg.FILE_DIR, cfg.CSV), "excel", cfg.EXPORT_FIELDS, "ab")
            status = sorted(eafile.status(cfg.EXPORT_FIELDS).items())
            print status
            csvfile.write([filename] + [str(v * 100) + "%" for (k, v) in status])



def cleanEaf(fname, template=None):
    eafile = eaf.Eaf(fname)

    if template is not None:
        eafile.importTypes(template)

    tids = eafile.getTierIds()
    spkrs = set([s.partition('@')[2] for s in tids])

    for s in spkrs:
        cleanEafBlock(eafile, s)

    return eafile


def cleanEafBlock(eafile, spkr=''):
    pass


if __name__ == "__main__":
    main()
