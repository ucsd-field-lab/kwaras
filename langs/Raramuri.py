# -*- coding: utf-8 -*-
'''
Created on March 22, 2013

@author: lucien
'''

import os, re
import xml.etree.ElementTree as etree
from formats import eaf


def Orth2IPA(u):
    u = u"" + u
    _orth_ = [
        {u"ch":u"tʃ",
        u"č":u"tʃ",
        u"sh":u"ʃ",
        u"š":u"ʃ",
        u"¢":u"ts",
   #     u"r":u"ɾ",
        u"y":u"j",
        u"'":u"ʔ"},
        {u"ɾɾ":u"r"},
        {u"á":u"ˈXa", # compound
         u"á":u"ˈXa",# combining
        u"é":u"ˈXe", # compound
        u"é":u"ˈXe",# combining
        u"í":u"ˈXi", # compound
        u"í":u"ˈXi",# combining
         u"ó":u"ˈXo", # compound
        u"ó":u"ˈXo", # combining
        u"ú":u"ˈXu", # compound
         u"ú":u"ˈXu"} # combining
        ]
    for oset in _orth_:
        for okey in oset:
            u = re.sub(okey,oset[okey],u)
    u = re.sub(u"([aeiouɪɛəɔʊ])[:ː]",u"\g<1>\g<1>",u) # recode length with double vowel
    u = re.sub(u"([^aeiouɪɛəɔʊ ])ˈX",u"ˈX\g<1>",u) # move the stress mark before C
    u = re.sub(u"tˈX",u"ˈXt",u) # move it again in the case of tʃ
    u = re.sub(u"X",u"",u) # take out the marker of a new stress mark
    return u

def cleanEaf(eafile):
    
    _orthtier = "Broad"
    _wordtier = "Word"
    
    # back up the orthographic tier
    bktier = eaf.copyTier(eafile, _orthtier, targ_id=_orthtier+"-bk",
                          parent=_orthtier, ltype="Free translation")
    eaf.insertTier(eafile,bktier,after=_orthtier)
    
    # use new orthography
    orthnotes = eaf.getTierById(eafile,_orthtier).iter("ANNOTATION_VALUE")
    for note in orthnotes:
        if note.text:
            print note.text, ":", repr(note.text)
            note.text = Orth2IPA(note.text)
            note.text = note.text.strip()
            print ">",note.text
            
    if _wordtier in eaf.getTierIds(eafile):
        wordnotes = eaf.getTierById(eafile,_wordtier).iter("ANNOTATION_VALUE")
    else:
        wordnotes = []
     
    for note in wordnotes:
        if note.text:
            print note.text, ":", repr(note.text)
            note.text = Orth2IPA(note.text)
            note.text = note.text.strip()
            print ">",note.text
            

    return eafile
                
if __name__ == "__main__":
    
    _FILE_DIR = "R://ELAN corpus/"
    _OLD_EAFS = ""
    _NEW_EAFS = "new/"

    for filename in os.listdir(os.path.join(_FILE_DIR,_OLD_EAFS)):
        print filename
        if os.path.splitext(filename)[1].lower() != ".eaf":
            print "Not an eaf:",filename,os.path.splitext(filename)
        else:
            fstr = open(os.path.join(_FILE_DIR,_OLD_EAFS,filename))
            eafile = etree.fromstring('\n'.join(fstr))
            eafile = cleanEaf(eafile)
            
            outstr = open(os.path.join(_FILE_DIR,_NEW_EAFS,filename),"w")
            outstr.write( etree.tostring(eafile) )
            outstr.close()
            
            
            
            