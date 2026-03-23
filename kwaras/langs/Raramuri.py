# -*- coding: utf-8 -*-
"""
Created on March 22, 2013

@author: lucien
"""

import csv
import os
import re
import json

from ..formats import eaf

_V_ = "aeiouɪɛəɔʊ"  # Vowels
_P_ = ",;?\.\)\(”“…"  # Punctuation NOTE: alternatively tokenize with:  .()”“…,?;
_C_ = "[^ " + _V_ + _P_ + "]"


def main():
    cfg_file = "config.txt"
    up_dir = os.path.dirname(os.getcwd())
    cfg = json.load(os.path.join(up_dir, cfg_file))
    csvfile = csv.writer(open(os.path.join(cfg["FILE_DIR"], "status.csv"), mode="a"))
    csvfile.writerow(["Filename"] + cfg["EXPORT_FIELDS"])

    for filename in os.listdir(os.path.join(cfg["FILE_DIR"], cfg["OLD_EAFS"])):
        print(filename)
        if not os.path.splitext(filename)[1].lower() == ".eaf":
            print("Not an eaf:", filename, os.path.splitext(filename))
        else:
            fpath = os.path.join(cfg["FILE_DIR"], cfg["OLD_EAFS"], filename)
            template = os.path.join(cfg["FILE_DIR"], cfg["TEMPLATE"])
            eafile = clean_eaf(fpath, template)
            eafile.write(os.path.join(cfg["FILE_DIR"], cfg["NEW_EAFS"], filename))
            eafile.export_to_csv(os.path.join(cfg["FILE_DIR"], cfg["CSV"]), "excel", cfg["EXPORT_FIELDS"], "ab")
            status = sorted(eafile.status(cfg["EXPORT_FIELDS"]).items())
            print(status)
            csvfile.writerow([filename] + [str(v * 100) + "%" for (k, v) in status])


def orth2IPA(u):
    u = "" + u
    _orth_ = [
        {"ch": "tʃ",
         "č": "tʃ",
         "sh": "ʃ",
         "š": "ʃ",
         "¢": "ts",
         "r": "ɾ",  # comment out to leave r ambiguous
         "y": "j",
         "'": "ʔ",
         "‘": "ʔ",
         "’": "ʔ"},
        {"ɾɾ": "r"},
        {"á": "ˈXa",  # compound
         "â": "ˈXa",
         "à": "ˈXa",
         "á": "ˈXa",  # combining
         "â": "ˈXa",
         "à": "ˈXa",
         "é": "ˈXe",  # compound
         "ê": "ˈXe",
         "è": "ˈXe",
         "é": "ˈXe",  # combining
         "ê": "ˈXe",
         "è": "ˈXe",
         "í": "ˈXi",  # compound
         "î": "ˈXi",
         "ì": "ˈXi",
         "í": "ˈXi",  # combining
         "î": "ˈXi",
         "ì": "ˈXi",
         "ó": "ˈXo",  # compound
         "ô": "ˈXo",
         "ò": "ˈXo",
         "ó": "ˈXo",  # combining
         "ô": "ˈXo",
         "ò": "ˈXo",
         "ú": "ˈXu",  # compound
         "û": "ˈXu",
         "ù": "ˈXu",
         "ú": "ˈXu",  # combining
         "û": "ˈXu",
         "ù": "ˈXu"}

    ]
    for oset in _orth_:
        for okey in oset:
            u = re.sub(okey, oset[okey], u)
    u = re.sub("[=\-\[\]]", "", u)
    # u = re.sub(u"(["+_V_+"])[:ː]",u"\g<1>\g<1>",u) # recode length with double vowel
    u = re.sub("([" + _V_ + "])ː", "\g<1>\g<1>", u)  # recode length with double vowel
    u = re.sub("(" + _C_ + ")ˈX", "ˈX\g<1>", u)  # move the stress mark before C
    u = re.sub("tˈX", "ˈXt", u)  # move it again in the case of tʃ
    u = re.sub("X", "", u)  # take out the marker of a new stress mark
    u = re.sub("/", " ", u)
    u = re.sub("((^| )ˈ?)ɾ", "\g<1>r", u)  # initial r are all /r/
    return u


def orth2NewOrth(u):
    u = "" + u
    _orth_ = [
        {"sh": "s",
         "š": "s"},
        {"ch": "<CH>"},
        {"j": "y"},
        {"h": "j"},  # TODO: preaspiration should be left as <h>
        {"<CH>": "ch",
         "č": "ch",
         "¢": "ch"},
        {"rr": "r"},
        {"-": "",
         "=": " "}
    ]
    # if "j" in u:
    #    print "Warning: I don't know which <j> this is"
    #    print u
    # if re.search("[\[\]\(\)]", u):
    #    print "Warning: There might be an inline comment"
    #    print u
    for oset in _orth_:
        for okey in oset:
            u = re.sub(okey, oset[okey], u)
    # u = re.sub(u"(["+_V_+"])[:ː]",u"\g<1>\g<1>",u) # recode length with double vowel
    u = re.sub("([" + _V_ + "])ː", "\g<1>\g<1>", u)  # recode length with double vowel
    return u


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
    if spkr != '':
        spkr = '@' + spkr

    _basetier = "Broad" + spkr
    _orthtier = "Ortho" + spkr
    _orth2tier = "NewOrtho" + spkr
    _wordtier = "Word" + spkr
    _glosstier = "Gloss" + spkr
    _morphtier = "Morph" + spkr
    _mcattier = "MCat" + spkr
    _uttwgltier = "UttWGloss" + spkr
    _uttmgltier = "UttMGloss" + spkr
    _uttgltier = "UttGloss" + spkr
    _transtiers = [tn + spkr for tn in ['English', 'Spanish']]
    _mglosstiers = [tn + spkr for tn in ['MGloss', 'MGloss-ES']]
    _notetier = "Note" + spkr

    if _basetier in eafile.get_tier_ids():
        # back up the baseline tier into @_orthtier, unless it already exists
        if _orthtier in eafile.get_tier_ids() and eafile.get_annotations_in(_orthtier) is []:
            # we have an empty orthtier -- move it out of the way
            orthbk = eafile.get_tier_by_id(_orthtier)
            eafile.rename_tier(orthbk, _orthtier + "_bk")
        if _orthtier not in eafile.get_tier_ids():
            # there is not yet an orthtier, so make it
            bktier = eafile.copy_tier(_basetier, targ_id=_orthtier,
                                      parent=_basetier, ltype="Alternate transcription")
            eafile.insert_tier(bktier, after=_basetier)

            # use IPA in baseline tier
            basenotes = eafile.get_tier_by_id(_basetier).iter("ANNOTATION_VALUE")
            for note in basenotes:
                if note.text:
                    # print note.text, ":", repr(note.text)
                    note.text = orth2IPA(note.text)
                    note.text = note.text.strip()
                    # print ">",note.text

    if _orthtier in eafile.get_tier_ids():
        if _orth2tier in eafile.get_tier_ids():
            print(_orth2tier, "already exists")
        else:
            neworth = eafile.copy_tier(_orthtier, targ_id=_orth2tier,
                                       parent=_basetier, ltype="Alternate transcription")
            eafile.insert_tier(neworth, after=_orthtier)
        onotes = eafile.get_tier_by_id(_orthtier).iter("[ANNOTATION_VALUE]")
        for on in onotes:
            print(on, on.tag, on.attrib)
            ontime = eafile.get_time(on)
            on2 = eafile.get_annotation_at(_orth2tier, ontime[0])
            if on.text:
                on2.findall("ANNOTATION_VALUE")[0].text = orth2NewOrth(on.findall("ANNOTATION_VALUE")[0].text)

    # use new orthography in words
    if _wordtier in eafile.get_tier_ids():
        wordnotes = eafile.get_tier_by_id(_wordtier).iter("ANNOTATION_VALUE")
        for note in wordnotes:
            if note.text:
                # print note.text, ":", repr(note.text)
                note.text = orth2IPA(note.text)
                note.text = re.sub("[" + _P_ + "]", " ", note.text).strip()
                note.text = note.text.strip()
                # print ">",note.text

    # make utterance-level gloss tier from word glosses
    if _uttwgltier not in eafile.get_tier_ids() and _glosstier in eafile.get_tier_ids():
        ugtier = eafile.copy_tier(_basetier, targ_id=_uttwgltier,
                                  parent=_basetier, ltype="Glosses")
        eafile.insert_tier(ugtier, after=_orthtier)
    if _uttwgltier in eafile.get_tier_ids() and eafile.get_annotations_in(_glosstier) is not []:
        for annot in eafile.get_annotations_in(_uttwgltier):
            times = eafile.get_time(annot)
            glosses = eafile.get_annotations_in(_glosstier, times[0], times[1])
            try:
                ug = [g.find("ANNOTATION_VALUE").text for g in glosses]
                ug = [g for g in ug if g is not None]
                annot.find("ANNOTATION_VALUE").text = ' '.join(ug)
            except:
                print("What's wrong here:", [g.find("ANNOTATION_VALUE").text for g in glosses])

    # make utterance-level gloss tier from morph glosses
    if _uttmgltier not in eafile.get_tier_ids() and _morphtier in eafile.get_tier_ids():
        umgltier = eafile.copy_tier(_basetier, targ_id=_uttmgltier,
                                    parent=_basetier, ltype="Glosses")
        eafile.insert_tier(umgltier, after=_orthtier)
    if _uttmgltier in eafile.get_tier_ids() and eafile.get_annotations_in(_morphtier) is not []:
        for annot in eafile.get_annotations_in(_uttmgltier):
            utttab = "<table><tr>"
            times = eafile.get_time(annot)
            words = eafile.get_annotations_in(_wordtier, times[0], times[1])
            for w in words:
                wtimes = eafile.get_time(w)
                tab = "<table>"
                for tier in [_morphtier]:  # [_morphtier, _mcattier]:
                    morphs = eafile.get_annotations_in(tier, wtimes[0], wtimes[1])
                    morphs = [m.find("ANNOTATION_VALUE").text for m in morphs]
                    morphs = [m for m in morphs if m is not None]
                    tab += "<tr><td>" + "</td><td>".join(morphs) + "</td></tr>"
                for tier in _mglosstiers:
                    morphs = eafile.get_annotations_in(tier, wtimes[0], wtimes[1])
                    morphs = [m.find("ANNOTATION_VALUE").text for m in morphs]
                    morphs = [m for m in morphs if m is not None]
                    tab += "<tr><td>" + "</td><td>".join(morphs) + "</td></tr>"
                tab += "</table>"
                utttab += "<td>" + tab + "</td>"
            utttab += "</tr></table>"
            annot.find("ANNOTATION_VALUE").text = utttab
            #             try:
            #                 ug = [m.find("ANNOTATION_VALUE").text for m in morphs]
            #                 ug = [m for m in ug if m is not None]
            #                 annot.find("ANNOTATION_VALUE").text = "<tr><td>"+"</td><td>".join(ug)+"</tr>"
            #             except:
            #                 print "What's wrong here:",[g.find("ANNOTATION_VALUE").text for g in glosses]
            #                 raise

    # make sure Note and Broad tiers are independent
    if _notetier in eafile.get_tier_ids():
        note_tier = eafile.get_tier_by_id(_notetier)
        eafile.change_parent(note_tier, None, "Note")
    if _basetier in eafile.get_tier_ids():
        broad_tier = eafile.get_tier_by_id(_basetier)
        eafile.change_parent(broad_tier, None, "Transcription")

    # make sure Spanish and English tiers are dependent
    for tn in _transtiers:
        if tn in eafile.get_tier_ids():
            tntier = eafile.get_tier_by_id(tn)
            eafile.change_parent(tntier, _basetier, "Free translation")


if __name__ == "__main__":
    main()
