# -*- coding: utf-8 -*-
"""
Created on March 22, 2013

@author: lucien
"""

import os
import re
import json

from ..formats import eaf, utfcsv

_V_ = u"aeiouɪɛəɔʊ"  # Vowels
_P_ = u",;?\.\)\(”“…"  # Punctuation NOTE: alternatively tokenize with:  .()”“…,?;
_C_ = u"[^ " + _V_ + _P_ + u"]"


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


def orth2IPA(u):
    u = u"" + u
    _orth_ = [
        {u"ch": u"tʃ",
         u"č": u"tʃ",
         u"sh": u"ʃ",
         u"š": u"ʃ",
         u"¢": u"ts",
         u"r": u"ɾ",  # comment out to leave r ambiguous
         u"y": u"j",
         u"'": u"ʔ",
         u"‘": u"ʔ",
         u"’": u"ʔ"},
        {u"ɾɾ": u"r"},
        {u"á": u"ˈXa",  # compound
         u"â": u"ˈXa",
         u"à": u"ˈXa",
         u"á": u"ˈXa",  # combining
         u"â": u"ˈXa",
         u"à": u"ˈXa",
         u"é": u"ˈXe",  # compound
         u"ê": u"ˈXe",
         u"è": u"ˈXe",
         u"é": u"ˈXe",  # combining
         u"ê": u"ˈXe",
         u"è": u"ˈXe",
         u"í": u"ˈXi",  # compound
         u"î": u"ˈXi",
         u"ì": u"ˈXi",
         u"í": u"ˈXi",  # combining
         u"î": u"ˈXi",
         u"ì": u"ˈXi",
         u"ó": u"ˈXo",  # compound
         u"ô": u"ˈXo",
         u"ò": u"ˈXo",
         u"ó": u"ˈXo",  # combining
         u"ô": u"ˈXo",
         u"ò": u"ˈXo",
         u"ú": u"ˈXu",  # compound
         u"û": u"ˈXu",
         u"ù": u"ˈXu",
         u"ú": u"ˈXu",  # combining
         u"û": u"ˈXu",
         u"ù": u"ˈXu"}

    ]
    for oset in _orth_:
        for okey in oset:
            u = re.sub(okey, oset[okey], u)
    u = re.sub(u"[=\-\[\]]", "", u)
    # u = re.sub(u"(["+_V_+"])[:ː]",u"\g<1>\g<1>",u) # recode length with double vowel
    u = re.sub(u"([" + _V_ + u"])ː", u"\g<1>\g<1>", u)  # recode length with double vowel
    u = re.sub(u"(" + _C_ + u")ˈX", u"ˈX\g<1>", u)  # move the stress mark before C
    u = re.sub(u"tˈX", u"ˈXt", u)  # move it again in the case of tʃ
    u = re.sub(u"X", u"", u)  # take out the marker of a new stress mark
    u = re.sub(u"/", " ", u)
    u = re.sub(u"((^| )ˈ?)ɾ", u"\g<1>r", u)  # initial r are all /r/
    return u


def orth2NewOrth(u):
    u = u"" + u
    _orth_ = [
        {u"sh": u"s",
         u"š": u"s"},
        {u"ch": u"<CH>"},
        {u"j": u"y"},
        {u"h": u"j"},  # TODO: preaspiration should be left as <h>
        {u"<CH>": u"ch",
         u"č": u"ch",
         u"¢": u"ch"},
        {u"rr": u"r"},
        {u"-": "",
         u"=": " "}
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
    u = re.sub(u"([" + _V_ + "])ː", u"\g<1>\g<1>", u)  # recode length with double vowel
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
            print _orth2tier, "already exists"
        else:
            neworth = eafile.copy_tier(_orthtier, targ_id=_orth2tier,
                                       parent=_basetier, ltype="Alternate transcription")
            eafile.insert_tier(neworth, after=_orthtier)
        onotes = eafile.get_tier_by_id(_orthtier).iter("[ANNOTATION_VALUE]")
        for on in onotes:
            print on, on.tag, on.attrib
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
                note.text = re.sub(u"[" + _P_ + "]", " ", note.text).strip()
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
                print "What's wrong here:", [g.find("ANNOTATION_VALUE").text for g in glosses]

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
