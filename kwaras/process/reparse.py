"""
Created on Nov 3, 2013

@author: lscarrol
"""
import re
from xml.etree import ElementTree as etree

from ..formats.lift import Lift
from ..formats.eaf import Eaf

_LANG = 1
_LANG_CODE = ("en", "es")[_LANG]
_MGLOSS_TIER = ("MGloss", "MGloss-ES")[_LANG]


def update(eafile, tiers, eafl):
    for m in eafile.get_annotations_in(tiers["m"]):
        timept = human_time(eafile.get_time(m)[0])
        x = eafile.get_annotation_on(tiers["x"], m)
        if x is not None:
            aval = x.findtext("ANNOTATION_VALUE")
            # print aval
            if aval is '':
                print("Blank X annotation:", etree.tostring(x))
                e = None
            else:
                gidm = re.search("\(([^.]*)\)", x.findtext("ANNOTATION_VALUE"))
                if gidm is None:
                    print("WARNING!")
                    print("Flaw in annotation:", aval, "at time", timept, "\n")
                    e = None
                else:
                    gid = gidm.group(1)
                    # print "gid found:",gid
                    e = eafl.getEntry(gid)

            if e is None:
                g = None
            else:
                sns = eafl.getSenses(gid)
                sense = sns[0]
                g = sense.find("gloss[@lang='{}']/text".format(_LANG_CODE))

            if g is None:
                gloss = eafile.get_annotation_on(tiers['g'], m)
                print("WARNING!")
                print("No gloss found for", gid, gloss.find("ANNOTATION_VALUE").text, end=' ')
                print("at time", timept, '\n')
                # gloss.find("ANNOTATION_VALUE").text = ""
            else:
                newg = g.text
                gloss = eafile.get_annotation_on(tiers['g'], m)
                if gloss is None:
                    print("WARNING!")
                    print("No existing gloss found for", gid, newg)
                elif newg != gloss.find("ANNOTATION_VALUE").text:
                    print(gloss.find("ANNOTATION_VALUE").text, "=>", newg)
                    gloss.find("ANNOTATION_VALUE").text = newg

    return eafile


def human_time(milliseconds):
    """Take a timsetamp in milliseconds and convert it into the familiar
    minutes:seconds format.

    Args:
        milliseconds: time expressed in milliseconds

    Returns:
        str, time in the minutes:seconds format

    For example:
    """
    milliseconds = int(milliseconds)

    seconds = milliseconds / 1000.0
    minutes = seconds / 60

    seconds = "{0:0>4.1f}".format(seconds % 60)
    minutes = str(int(minutes))

    return minutes + ':' + seconds


if __name__ == '__main__':
    testfile = r"C:\Users\Public\Documents\ELAN\texts\tx_maiwaachi.eaf"
    outfile = r"C:\Users\Public\Documents\ELAN\texts\temp\tx_maiwaachi.eaf"
    lexicon = r"C:\Users\Public\Documents\ELAN\ELAN.lift"

    eafile = Eaf(testfile)
    eafl = Lift(lexicon)
    tiernames = {"m": "Morph", "g": _MGLOSS_TIER, "x": "MCat"}
    eafile = update(eafile, tiernames, eafl)
    eafile.write(outfile)
