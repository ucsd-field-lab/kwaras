# -*- coding: utf-8 -*-
'''
Created on Jul 27, 2012

@author: lucien
'''

import os, re
import xml.etree.ElementTree as etree
from formats import eaf

_FILE_DIR = "/Users/lucien/Data/Mixtec/Transcriptions"
_OLD_EAFS = "originals July2012"
_NEW_EAFS = "test"

# orthographic correspondences
_SPELLING = [    # steps required to prevent transitive ʃ → x → j → y
          { "ʒ":"y",        # ʒ
            "j":"y",         # j
            "ʲ":"y",        # sup j → y
            "ʑ":"y"
        }, {
            "ʰ":"",         # sup h
            "x":"j",         # x
            "h":"j"         # h
        }, {
            "ɲ":"ñ",   # ñ
            "ny":"ñ",
            "ʔ":"'",    # glottal stop
            "ʃ":"x",    # esh
            "ʷ":"w",    # sup w
            "β":"v",     # beta → v
            "ɾ":"r",    # flap
            "ɽ":"r",    # retroflex flap
            "ⁿ":"n",    # sup n
            "ŋ":"n"     # engma → n
        }, {
            "̃":"N",    # nasalization
            "᷈":"N",
            "᷉":"N",
            "˜u":"uN",
            "ũ":"uN",
            "ã":"aN",
            "ẽ":"eN",
            "˜i":"iN",
            "ĩ":"iN",
            "ɪ":"ɨ",   # I
            "ɛ":"e",       # E
            "ɔ":"o",       # open O
            "ə":"ɨ",   # schwa
            "ɑ":"a",       # A
            u"\xe1":"a",     # accented a
            u"\xf3":"o",     # accented o
            u"\xe9":"e",     # accented e
            u"\xfa":"u",     # accented u
            u"\xed":"i",     # accented i
            "¹":"",        # sup 1
            "²":"",        # sup 2
            "³":"",        # sup 3
            "⁴":"",       # sup 4
            "⁵":"",       # sup 5
            "́":"",        # acute accent
            "̀":"",         # grave accent
            "͡":"",         # overbrace
            "̪":"",      # dental sign
            "̽":"",          # combining X ??
            "̤":""          # breathy voice
            }
        ]

def cleanEaf(eafile):

    #ipa = eaf.getTierById(eafile, "IPA Transcription")
    #print eaf, ipa
    #print ipa.attrib

    eaf.renameTier(eaf.getTierById(eafile, "IPA Transcription"), "Orthographic", eafile)
    try:
        eaf.renameTier(eaf.getTierById(eafile, "Traslation (English)"), "Translation (English)", eafile)
    except:
        print "Spelling is previously fixed."
    
    # copy old IPA transcription to new tier
    phontier = eaf.copyTier(eaf.getTierById(eafile, "Orthographic"),targ_id= "Phonetic",parent= "Orthographic",ltype= "Words")
    eaf.insertTier(eafile,phontier,after=eaf.getTierById(eafile,"Orthographic"))

    # add tone tier
    tonetier = etree.fromstring("""
        <TIER DEFAULT_LOCALE="en" LINGUISTIC_TYPE_REF="Words" PARENT_REF="Orthographic" TIER_ID="Tone" />
    """)
    eaf.insertTier(eafile,tonetier)
    
    # remove participant Rodgriguez
    for t in eafile.iter("TIER"):
        if t.get("PARTICIPANT") == "Hector Rodriguez":
            t.set("PARTICIPANT","")
    
    # use new orthography
    orthnotes = eaf.getTierById(eafile,"Orthographic").iter("ANNOTATION_VALUE")
    for note in orthnotes:
        if note.text:
            print note.text, ":", repr(note.text)
            for step in _SPELLING:
                for key in step:
                    note.text = note.text.replace(key,step[key])
                    #print ">",note.text
            note.text = re.sub("[0-9]","",note.text)
            note.text = note.text.replace(".","")
            note.text = note.text.replace("()","")
        
            note.text = re.sub("N+","N",note.text)
            note.text = re.sub("N('[aeiou]N)",r"\1",note.text)
            note.text = re.sub("([aeiou])N([aeiou])",r"\1\2",note.text)
            note.text = re.sub("N","ⁿ",note.text)
            print ">",note.text
     
    return eafile
                
if __name__ == "__main__":
    
    
    for filename in os.listdir(os.path.join(_FILE_DIR,_OLD_EAFS))[:3]:
        print filename
        if os.path.splitext(filename)[1].lower() != ".eaf":
            print "Not an EAF:",filename,os.path.splitext(filename)
        else:
            fstr = open(os.path.join(_FILE_DIR,_OLD_EAFS,filename))
            eafile = etree.fromstring('\n'.join(fstr))
            eafile = cleanEaf(eafile)
            
            outstr = open(os.path.join(_FILE_DIR,_NEW_EAFS,filename),"w")
            outstr.write( etree.tostring(eafile) )
            outstr.close()
            
            
            
            