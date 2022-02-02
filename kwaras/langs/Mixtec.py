# -*- coding: utf-8 -*-
"""
Created on Jul 27, 2012

@author: lucien
"""

import os
import re

from ..formats import eaf

# orthographic correspondences
_SPELLING = [  # steps required to prevent transitive ʃ → x → j → y
    {"ʒ": "y",  # ʒ
     "j": "y",  # j
     "ʲ": "y",  # sup j → y
     "ʑ": "y",
     "ʤ": "dy",
     "ʧ": "ty"
     }, {
        "ʰ": "",  # sup h
        "x": "j",  # x
        "χ": "j",
        "h": "j"  # h
    }, {
        "ɲ": "ñ",  # ñ
        "ny": "ñ",
        "ñ": "ñ",
        "ʔ": "'",  # glottal stop
        "ʃ": "x",  # esh
        "ʷ": "u",  # sup w
        "w": "u",
        "β": "v",  # beta → v
        "ɾ": "r",  # flap
        "ɽ": "r",  # retroflex flap
        "ⁿ": "n",  # sup n
        "ŋ": "n"  # engma → n
    }, {
        "tx": "ch",
        "̃": "N",  # nasalization
        "᷈": "N",
        "᷉": "N",
        # "˜u":"uN",
        "ũ": "uN",
        "ã": "aN",
        "ẽ": "eN",
        "õ": "oN",
        # "˜i":"iN",
        "ĩ": "iN",
        "ɪ": "ɨ",  # I
        "ɛ": "e",  # E
        "ɔ": "o",  # open O
        "ə": "ɨ",  # schwa
        "ɑ": "a",  # A
        "\xe1": "a",  # accented a
        "\xf3": "o",  # accented o
        "\xe9": "e",  # accented e
        "\xfa": "u",  # accented u
        "\xed": "i",  # accented i
        "¹": "",  # sup 1
        "²": "",  # sup 2
        "³": "",  # sup 3
        "⁴": "",  # sup 4
        "⁵": "",  # sup 5
        "́": "",  # acute accent
        "̀": "",  # grave accent
        "͡": "",  # overbrace
        "̪": "",  # dental sign
        "̽": "",  # combining X ??
        "̤": ""  # breathy voice
    }
]

_TO_IPA = [
    {"dy": "dʲ",
     "ty": "tʲ",
     "ch": "tʃ",
     "nd": "ⁿd"},
    {"y": "ʒ",
     "j": "h",
     "ñ": "ɲ",
     "ñ": "ɲ",
     "'": "ʔ",
     "x": "ʃ",
     "w": "ʷ",
     "r": "ɾ"}
]


def convert_to_ipa(text):
    text = text.decode("utf-8").strip()
    print(text, ":", repr(text))
    for step in _TO_IPA:
        for key in step:
            text = text.replace(key, step[key])

    text = re.sub("n(-| |$)", r"N\1", text)
    print(repr(text), "> ", end=' ')
    text = re.sub("([aeiouɨ])([mnɲ][aeiouɨ])(-| |$)", r"\1N\2N\3", text)  # spread from mid C
    text = re.sub("([aeiɨou])(ʔ[mnɲ][aeiouɨ])(-| |$)", r"\1N\2N\3", text)  # spread from mid C
    print(text, "> ", end=' ')
    text = re.sub("([aeiɨou])([aeiɨou]N)", r"\1N\2", text)  # spread L from final vowel
    text = re.sub("([aeiɨou])(ʔ[aeiɨou]N)", r"\1N\2", text)  # spread L from final vowel
    print(text, "> ", end=' ')
    text = re.sub("([mnɲ][aeiɨou])", r"\1N", text)  # spread R from onset
    text = re.sub("(N(ʔ)?[aeiɨou])", r"\1N", text)  # spread R from initial vowel
    text = re.sub("N+", r"̃", text)

    text += " *"  # mark automated transcriptions
    print(text)
    return text


def convert_to_ortho(text):
    text = text.decode("utf-8").strip()
    print(text, ":", repr(text))
    for step in _SPELLING:
        for key in step:
            text = text.replace(key, step[key])
            # print ">",text
    text = re.sub("[0-9]", "", text)
    text = text.replace(".", "")
    text = text.replace("()", "")

    text = re.sub("([aeiɨou]):", r"\1\1", text)

    text = re.sub("N+", "N", text)
    text = re.sub("N('?[aeiɨou]N)", r"\1", text)  # vowel to vowel nasalization
    text = re.sub("N('?[mnñ])", r"\1", text)  # C to V leftward
    text = re.sub("([mnñ][aeiɨou])N", r"\1", text)  # C to V rightward
    text = re.sub("([aeiɨou])N([aeiɨou])", r"\1\2", text)  # vowel to vowel
    text = re.sub("N( |$)", r"n\1", text)  # nasalization at word end
    text = re.sub("N", "n-", text)  # nasalization mid-word
    text += " *"  # mark automated transcriptions
    print(">", text)
    return text


def clean_eaf(fname, template=None):
    eafile = eaf.Eaf(fname)
    tiers = eafile.get_tier_ids()
    has_ortho = ("Orthographic" in tiers and
                 len([eafile.get_tier_by_id("Orthographic").iter("ANNOTATION_VALUE")]) > 0)
    has_ipa = ("IPA Transcription" in tiers and
               len([eafile.get_tier_by_id("IPA Transcription").iter("ANNOTATION_VALUE")]) > 0)
    has_phon = ("Phonetic" in tiers and
                len([eafile.get_tier_by_id("Phonetic").iter("ANNOTATION_VALUE")]) > 0)

    if has_ortho and not has_phon:
        # generate phonetic transcription from orthographic transcription
        if "Phonetic" in eafile.get_tier_ids():
            eafile.rename_tier(eafile.get_tier_by_id("Phonetic"), "Phonetic-bk")  # should be blank tiers only

        phontier = eafile.copy_tier("Orthographic", "Phonetic",
                                    parent="Orthographic", ltype="Alternate transcription")
        eafile.insert_tier(phontier, after="Orthographic")

        # use IPA
        phonnotes = eafile.get_tier_by_id("Phonetic").iter("ANNOTATION_VALUE")
        for note in phonnotes:
            if note.text is not None:
                note.text = convert_to_ipa(note.text)

    elif has_ipa and not has_ortho:
        # generate orthographic transcription from phonetic transcription

        if has_phon:
            phonnotes = eafile.get_tier_by_id("Phonetic").iter("ANNOTATION_VALUE")
            print(phonnotes[:5])
            raise Exception
        if "Orthographic" in eafile.get_tier_ids():
            eafile.rename_tier(eafile.get_tier_by_id("Orthographic"), "Orthographic-bk")  # should be blank tiers only

        eafile.rename_tier(eafile.get_tier_by_id("IPA Transcription"), "Orthographic")

        # copy old IPA transcription to new dependent tier
        phontier = eafile.copy_tier("Orthographic", "Phonetic",
                                    parent="Orthographic", ltype="Alternate transcription")
        eafile.insert_tier(phontier, after="Orthographic")

        # use new orthography
        orthnotes = eafile.get_tier_by_id("Orthographic").iter("ANNOTATION_VALUE")
        for note in orthnotes:
            if note.text is not None:
                note.text = convert_to_ortho(note.text)

    elif has_phon and not has_ortho:  # i.e. "Phonetic" is baseline transcription

        if "Orthographic" in eafile.get_tier_ids():
            eafile.rename_tier(eafile.get_tier_by_id("Orthographic"), "Orthographic-bk")  # should be blank tiers only

        eafile.rename_tier(eafile.get_tier_by_id("Phonetic"), "Orthographic")

        # copy old IPA transcription to new dependent tier
        phontier = eafile.copy_tier("Orthographic", "Phonetic",
                                    parent="Orthographic", ltype="Alternate transcription")
        eafile.insert_tier(phontier, after="Orthographic")

        # use new orthography
        orthnotes = eafile.get_tier_by_id("Orthographic").iter("ANNOTATION_VALUE")
        for note in orthnotes:
            if note.text is not None:
                note.text = convert_to_ortho(note.text)

    # else: # both Phon and Ortho tiers already exist, but some may be empty in places
    #    phonnotes = eafile.get_tier_by_id("Phonetic").iter("ANNOTATION_VALUE")

    # standardize other tier names
    if "Traslation (English)" in eafile.get_tier_ids():
        eafile.rename_tier(eafile.get_tier_by_id("Traslation (English)"), "Translation (English)")
    else:
        print("Tier name spelling is previously fixed.")

    if "Translation (English)" in eafile.get_tier_ids():
        eafile.rename_tier(eafile.get_tier_by_id("Translation (English)"), "English")

    if "Translation (Spanish)" in eafile.get_tier_ids():
        eafile.rename_tier(eafile.get_tier_by_id("Translation (Spanish)"), "Spanish")

    if "Annotation (Other)" in eafile.get_tier_ids():
        eafile.rename_tier(eafile.get_tier_by_id("Annotation (other)"), "Note")

    # remove participant Rodgriguez
    for t in eafile.get_tier_ids():
        tier = eafile.get_tier_by_id(t)
        if tier.get("PARTICIPANT") == "Hector Rodriguez":
            tier.set("PARTICIPANT", "")

    return eafile


if __name__ == "__main__":
    _FILE_DIR = "/Users/lucien/Data/Mixtec/Transcriptions"
    _TEMPLATE = "ELAN template/mixteco3.etf"
    _OLD_EAFS = "originals"
    _NEW_EAFS = "test"
    _CSV = "min-new.csv"
    _EXPORT_FIELDS = ["Orthographic", "Phonetic", "Spanish", "English", "Semantic domain", "Note", "Tone"]

    for filename in os.listdir(os.path.join(_FILE_DIR, _OLD_EAFS))[:]:
        print(filename)
        if os.path.splitext(filename)[1].lower() != ".eaf":
            print("Not an EAF:", filename, os.path.splitext(filename))
        else:
            eafile = eaf.Eaf(os.path.join(_FILE_DIR, _OLD_EAFS, filename))
            eafile.import_types(os.path.join(_FILE_DIR, _TEMPLATE))
            eafile = clean_eaf(eafile)
            eafile.write(os.path.join(_FILE_DIR, _NEW_EAFS, filename))
            eafile.export_to_csv(os.path.join(_FILE_DIR, _CSV), "excel", _EXPORT_FIELDS, "ab")
