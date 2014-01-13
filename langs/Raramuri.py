# -*- coding: utf-8 -*-
'''
Created on March 22, 2013

@author: lucien
'''

import os, re
from formats import eaf, utfcsv

_V_ = "aeiouɪɛəɔʊ" # Vowels
_P_ = ",;?\.\)\(”“…" # Punctuation NOTE: alternatively tokenize with:  .()”“…,?;
_C_ = "[^ "+_V_+_P_+"]"

def Orth2IPA(u):
    u = u"" + u
    _orth_ = [
        {u"ch":u"tʃ",
        u"č":u"tʃ",
        u"sh":u"ʃ",
        u"š":u"ʃ",
        u"¢":u"ts",
        u"r":u"ɾ",    # comment out to leave r ambiguous
        u"y":u"j",
        u"'":u"ʔ",
        u"‘":u"ʔ",
        u"’":u"ʔ"},
        {u"ɾɾ":u"r"},
        {u"á":u"ˈXa", # compound
         u"â":u"ˈXa",
         u"à":u"ˈXa",         
         u"á":u"ˈXa",# combining
         u"â":u"ˈXa",
         u"à":u"ˈXa",
        u"é":u"ˈXe", # compound
        u"ê":u"ˈXe", 
        u"è":u"ˈXe",         
        u"é":u"ˈXe",# combining
        u"ê":u"ˈXe",
        u"è":u"ˈXe",
        u"í":u"ˈXi", # compound
        u"î":u"ˈXi", 
        u"ì":u"ˈXi", 
        u"í":u"ˈXi",# combining
        u"î":u"ˈXi",
        u"ì":u"ˈXi",
         u"ó":u"ˈXo", # compound
         u"ô":u"ˈXo", 
         u"ò":u"ˈXo",          
        u"ó":u"ˈXo", # combining
        u"ô":u"ˈXo",
        u"ò":u"ˈXo",
        u"ú":u"ˈXu", # compound
        u"û":u"ˈXu", 
        u"ù":u"ˈXu",                 
         u"ú":u"ˈXu", # combining
         u"û":u"ˈXu",
         u"ù":u"ˈXu"}
              
        ]
    for oset in _orth_:
        for okey in oset:
            u = re.sub(okey,oset[okey],u)
    u = re.sub(u"[=\-\[\]]","",u)
    u = re.sub(u"(["+_V_+"])[:ː]",u"\g<1>\g<1>",u) # recode length with double vowel
    u = re.sub(u"("+_C_+")ˈX",u"ˈX\g<1>",u) # move the stress mark before C
    u = re.sub(u"tˈX",u"ˈXt",u) # move it again in the case of tʃ
    u = re.sub(u"X",u"",u) # take out the marker of a new stress mark
    u = re.sub(u"\/"," ",u)
    u = re.sub(u"((^| )ˈ?)ɾ",u"\g<1>r",u) # initial r are all /r/
    return u

def cleanEaf(filename, template):
    
    _basetier = "Broad"
    _orthtier = "Ortho"
    _wordtier = "Word"
    _glosstier = "Gloss"
    _uttglosstier = "UttGloss"
    
    eafile = eaf.Eaf(filename)
    
    eafile.importTypes(template)

    # back up the baseline tier into @_orthtier, unless it already exists
    if (_orthtier in eafile.getTierIds() and eafile.getAnnotationsIn(_orthtier) is []):
        orthbk = eafile.getTierById(_orthtier)
        eafile.renameTier(orthbk,_orthtier+"_bk")
    if (_orthtier not in eafile.getTierIds()): 
        #and eafile.getAnnotationsIn(_orthtier) is not []):
                    
        bktier = eafile.copyTier(_basetier, targ_id=_orthtier,
                              parent=_basetier, ltype="Alternate transcription")
        eafile.insertTier(bktier,after=_basetier)
        
        # use new orthography
        basenotes = eafile.getTierById(_basetier).iter("ANNOTATION_VALUE")
        for note in basenotes:
            if note.text:
                #print note.text, ":", repr(note.text)
                note.text = Orth2IPA(note.text)
                note.text = note.text.strip()
                #print ">",note.text
            
    # use new orthography in words
    if _wordtier in eafile.getTierIds():
        wordnotes = eafile.getTierById(_wordtier).iter("ANNOTATION_VALUE")
    else:
        wordnotes = []
     
    for note in wordnotes:
        if note.text:
            #print note.text, ":", repr(note.text)
            note.text = Orth2IPA(note.text)
            note.text = re.sub(u"["+_P_+"]"," ",note.text).strip()
            note.text = note.text.strip()
            #print ">",note.text
                
    # make utterance-level gloss tier
    if (_uttglosstier in eafile.getTierIds() 
        and eafile.getAnnotationsIn(_uttglosstier) is not []):
        ugtier = eafile.copyTier(_basetier, targ_id=_uttglosstier,
                                 parent=_basetier, ltype="Glosses")
        eafile.insertTier(ugtier,after=_orthtier)
        for annot in eafile.getAnnotationsIn(_uttglosstier):
            times = eafile.getTime(annot)
            glosses = eafile.getAnnotationsIn(_glosstier,times[0],times[1])
            ug = ' '.join([g.find("ANNOTATION_VALUE").text for g in glosses])
            annot.find("ANNOTATION_VALUE").text = ug
        
    # make sure Note and Broad tiers are independent
    if "Note" in eafile.getTierIds():
        notetier = eafile.getTierById("Note")
        eafile.changeParent(notetier, None, "Note")
    if "Broad" in eafile.getTierIds():
        broadtier = eafile.getTierById("Broad")
        eafile.changeParent(broadtier, None, "Transcription")
    
    # make sure Spanish and English tiers are dependent
    if "Spanish" in eafile.getTierIds():
        spanishtier = eafile.getTierById("Spanish")
        eafile.changeParent(spanishtier, _basetier, "Free translation")
    if "English" in eafile.getTierIds():
        englishtier = eafile.getTierById("English")
        eafile.changeParent(englishtier, _basetier, "Free translation")
                
            
    return eafile
                
if __name__ == "__main__":
    
    _FILE_DIR = "R://ELAN corpus/"
    # _FILE_DIR = "/Users/lucien/Data/Raramuri/ELAN corpus/"
    #_FILE_DIR = r"C:\Users\Public\Documents\Alignment"
    _OLD_EAFS = ("","co","el","tx","new")[0]
    
    _NEW_EAFS = "new/"
    _TEMPLATE = "bk2/tx1.eaf"
    _CSV = "rar-new.csv"
    _EXPORT_FIELDS = ["Broad","Ortho","Phonetic","UttGloss","Spanish","English","Note","UttType"]

    csvfile = utfcsv.UnicodeWriter(os.path.join(_FILE_DIR,"status.csv"), "excel", mode="ab")
    csvfile.write(["Filename"]+_EXPORT_FIELDS)
    
    for filename in os.listdir(os.path.join(_FILE_DIR,_OLD_EAFS)):
        print filename
        if os.path.splitext(filename)[1].lower() != ".eaf":
            print "Not an eaf:",filename,os.path.splitext(filename)
        else:
            fpath = os.path.join(_FILE_DIR, _OLD_EAFS, filename)
            template = os.path.join(_FILE_DIR, _TEMPLATE)
            eafile = cleanEaf(fpath, template)
            eafile.write(os.path.join(_FILE_DIR, _NEW_EAFS, filename))
            eafile.exportToCSV(os.path.join(_FILE_DIR,_CSV), "excel", _EXPORT_FIELDS, "ab")
            status = [eafile.status(_EXPORT_FIELDS)[f] for f in _EXPORT_FIELDS]
            print eafile.status(_EXPORT_FIELDS)
            print status
            csvfile.write([filename]+[str(v*100)+"%" for v in status])

            
            