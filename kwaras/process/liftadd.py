# -*- coding: utf-8 -*-
"""
Created on Apr 16, 2013

@author: lucien
"""

import re

from kwaras.formats.lift import Lift


def expose_guid(lift):
    for lex, eid in list(lift.lexemes.items()):
        guid = lift.getField(eid, "GUID")
        print(guid.find("form/text").text)
        guid.find("form/text").text = eid.split("_")[-1]
        print(eid)
        print(guid)

    return lift


def add_allomorphs(lift):
    _V_ = "aeiouɪɛəɔʊ"

    for lex, eid in list(lift.lexemes.items()):
        # get list of forms (pronunciations plus allomorphs)
        forms = lift.getVarForms(eid)
        # print forms

        newforms = []
        # for any monosyllabic forms, suggest forms with and without stress
        for f in forms:
            m = re.search("^[^" + _V_ + "]*[" + _V_ + "][^" + _V_ + "]*$", f)
            if m:
                nostress = re.sub("ˈ", "", f)
                sep = re.match("([-=]?)(.*)", nostress)
                wstress = sep.group(1) + "ˈ" + sep.group(2)
                newforms += [nostress, wstress]

        # for any suggested forms not already in the list of forms, add them
        newforms = [f for f in newforms if f not in forms]
        print("forms:", forms, "newforms:", newforms)
        for f in newforms:
            lift.appendVariant(eid, f)
        forms += newforms

        newforms = []
        # for any forms that have /r/ or /l/, suggest [ɾ]
        for f in forms:
            m = re.search("r", f)
            if m:
                newforms += [re.sub("r", "ɾ", f)]
            m = re.search("l", f)
            if m:
                newforms += [re.sub("l", "ɾ", f)]

        # for any suggested forms not already in the list of forms, add them
        newforms = [f for f in newforms if f not in forms]
        for f in newforms:
            lift.appendVariant(eid, f)
        forms += newforms

        newforms = []
        # for any forms that have /ʃ/ (but not /tʃ/), suggest /s/
        for f in forms:
            m = re.search("^ʃ", f)
            if m:
                newforms += [re.sub("^ʃ", "s", f)]
            m = re.search("(?<!t)ʃ", f)
            if m:
                newforms += [re.sub("(?<!t)ʃ", "s", f)]

        # for any forms that have /s/ before /u/ or /i/, suggest /ʃ/
        for f in forms:
            m = re.search("s[iu]", f)
            if m:
                newforms += [re.sub("s(?=[iu])", "ʃ", f)]

        # for any suggested forms not already in the list of forms, add them
        newforms = [f for f in newforms if f not in forms]
        for f in newforms:
            lift.appendVariant(eid, f)
        forms += newforms

        newforms = []
        # for any forms that have final stress, suggest forms with long vowels
        for f in forms:
            m = re.search("ˈ[^{V}]*([{V}])$".format(V=_V_), f)
            if m:
                # print f, m.group()
                newforms += [f + m.group(1)]
                # else:
                # print f, "no match"
        # for any forms that have penultimate stress, suggest deleted vowels
        for f in forms:
            m = re.search("ˈ[^{V}]*[{V}][^{V}][ʃ]?([{V}])$".format(V=_V_), f)
            if m:
                # print f, m.group()
                newforms += [f[:-1]]
                # else:
                # print f, "no match"

        # for any suggested forms not already in the list of forms, add them
        # print newforms
        newforms = [f for f in newforms if f not in forms]
        for f in newforms:
            lift.appendVariant(eid, f)

    return lift


if __name__ == "__main__":
    import sys
    import os

    dirname = os.path.dirname(sys.argv[-1])

    for fname in os.listdir(dirname):
        base, ext = os.path.splitext(fname)
        if ext == ".lift":
            print("Exposing GUID as lexeme field in", fname)
            lift = Lift(os.path.join(dirname, fname))
            lift = expose_guid(lift)
            lift.write(os.path.join(dirname, base + "-guid.lift"))
            print("Data written to", os.path.join(dirname, base + "-guid.lift"))

            print("Adding allormorphs to", fname)
            # add allomorphs to LIFT file
            lift = add_allomorphs(lift)
            # dump the LIFT data to a new file
            lift.write(os.path.join(dirname, base + "-added.lift"))
            print("Data written to", os.path.join(dirname, base + "-added.lift"))

            print("Converting LIFT format to EAFL format")
            lift.toEAFL(os.path.join(dirname, base + "-import.eafl"))
            print("Data written to", os.path.join(dirname, base + "-import.eafl"))
        else:
            print("Not converting", fname, "with extension:", ext)
