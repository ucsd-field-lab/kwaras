# -*- coding: utf-8 -*-
'''
Created on August 4, 2012

@author: lucien
'''

import os, re
import xml.etree.ElementTree as etree
from formats.eaf import getTierById

_FILE_DIR = "/Users/lucien/Data/Gitonga/my clips/"
_OLD_EAFS = "temp"
_NEW_EAFS = "new3"

# orthographic correspondences
_SPELLING = [   
             { "ʰ":"h",
              "ʷ":"w",
              "ˠ":"w",
              "ŋ":"n",
              "N":"ɲ",
              "V":"v",
              "B":"β",
              "ɽ":"l"},
             { "ʝi":"ɣi" },
             { "ʝ":"ɣj",
              "ɣwu":"ɣu" },
             { "xxx":"",
              "̪":""}
             ]

_COMMENT = re.compile(" ?(\[[a-z]+\])")

def cleanEaf(eaf):
    
    # use new orthography
    orthnotes = getTierById(eaf,"Transcription").iter("ANNOTATION_VALUE")
    for note in orthnotes:
        if note.text:
            print note.text, ":", repr(note.text)

            for step in _SPELLING:
                for key in step:
                    note.text = note.text.replace(key,step[key])
                    #print ">",note.text
            note.text = re.sub("[0-9]","",note.text)
            
            note.text = re.sub("Q","[Q]",note.text)
            note.text = re.sub("S","[S]",note.text)
            
            if _COMMENT.match(note.text):
                note.text = _COMMENT.sub("",note.text) + _COMMENT.match(note.text).group()
            
            note.text = note.text.strip()
                            
            if note.text.endswith("wh"):
                note.text = note.text[:-2] + "[wh]"
            
            print ">",note.text
     
    return eaf
                
if __name__ == "__main__":
    
    
    for filename in os.listdir(os.path.join(_FILE_DIR,_OLD_EAFS)):
        print filename
        if os.path.splitext(filename)[1].lower() != ".eaf":
            print "Not an eaf:",filename,os.path.splitext(filename)
        else:
            fstr = open(os.path.join(_FILE_DIR,_OLD_EAFS,filename))
            eaf = etree.fromstring('\n'.join(fstr))
            eaf = cleanEaf(eaf)
            
            outstr = open(os.path.join(_FILE_DIR,_NEW_EAFS,filename),"w")
            outstr.write( etree.tostring(eaf) )
            outstr.close()
            
            
            
            