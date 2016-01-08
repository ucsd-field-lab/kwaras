#! env python2.7
__author__ = 'Lucien'

import argparse

try:
    import kwaras
except ImportError as e:
    import tkMessageBox

    tkMessageBox.showerror(title="Package not installed.",
                           message="The 'kwaras' package has not been installed yet. "
                                   "Run installer before running this.")
    raise e


def convert_lexicon():
    import os.path
    import json
    from kwaras.conf import config
    from kwaras.formats.lift import Lift
    from kwaras.process import liftadd

    config.ConfigWindow("lexicon.cfg", parts=["EAFL"])

    cfg = json.load(open("lexicon.cfg"))
    dir_name = cfg["EAFL_DIR"]
    inf_name = cfg["LIFT"]

    base, ext = os.path.splitext(inf_name)
    if ext == ".lift":
        print "Exposing GUID as field in", inf_name
        # update GUID field in lexicon
        lift = Lift(inf_name)
        lift = liftadd.exposeGuid(lift)
        lift.write(os.path.join(dir_name, base + "-guid.lift"))

        # add allomorphs to LIFT file
        print "Adding allomorphs to", inf_name
        lift = liftadd.addRarAllomorphs(lift)
        # dump the LIFT data to a new file
        outf_name = os.path.join(dir_name, base + "-added.lift")
        lift.write(outf_name)
        print "Data written to", outf_name

        print "Converting LIFT format to EAFL format"
        eafl_name = os.path.join(dir_name, base + "-import.eafl")
        lift.toEAFL(eafl_name)
        print "Data written to", eafl_name
    else:
        import tkMessageBox
        tkMessageBox.showerror(title="Wrong format.",
                               message="The selected file is not a LIFT lexicon file.")


def main(args):
    if args.convert_lexicon:
        convert_lexicon()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--convert-lexicon", action="store_true",
                        help="Convert FLEx LIFT lexicon to ELAN-Corpa EAFL lexicon")
    parser.add_argument("--export-corpus", action="store_true",
                        help="Export an ELAN corpus as web interface files")
    parser.add_argument("--reparse-corpus", action="store_true",
                        help="Update a parsed ELAN corpus with fresh lexicon data")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args)
