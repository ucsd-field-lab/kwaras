#! python
# -*- coding: utf-8 -*-
'''
Created on Dec 7, 2012

@author: lucien
'''

import sys
import os

import easygui as eg
from src.process import web

_WRK_DIR_ = "~/Data/"

def defineDomain(dtype,ext):
    ext = '.' + ext.lower().strip('.')
    
    typebox = eg.buttonbox("Is the domain of {} files defined by a (set of) files or by a directory?".format(dtype),
                "Where are the {} files?".format(dtype),["File","Directory"])
    
    if typebox == "File":
        filenames = eg.fileopenbox(title="Choose the {} file(s) to search for:".format(type),
                                  msg="Choose a file",default=_WRK_DIR_,multiple=True)
        filenames = [c for c in filenames if c.lower().endswith(ext)]
    else:
        filedir = eg.diropenbox(title="Choose a directory of {} files".format(type), 
                             msg="Choose a directory",default=_WRK_DIR_)
        if filedir:
            filenames = [os.path.join(filedir,c) for c in os.listdir(filedir) if c.lower().endswith(ext)]
        else:
            filenames = []
        
    return filenames

def exportHtml():
    web.main()
    
def convertTrans():
    pass

def changeAttr():
    
    eafnames = defineDomain("ELAN","eaf")
    
    chosen = eg.indexbox("What type of change do you want to make?","Edit type:",
                           ["Back","Add Tier"])
    
    if chosen:
        (addTier,)[chosen-1](eafnames)
        
def addTier(domain):
    from src.formats import eaf

    tierids = eaf.getTierIds(eaf.open(domain[0]))
    idcnt = dict(zip(tierids,[1]*len(tierids)))
    
    for eafn in domain:
        ids = eaf.getTierIds(eaf.open(eafn))
        for i in ids:
            idcnt[i] = idcnt.get(i,0) + 1
            if i not in tierids:
                tierids.append(i)
    
    stdCnt = max([idcnt[t] for t in tierids])
    stdTiers = [t for t in tierids if idcnt[t] == stdCnt]
                
    tierArgs = []
    while not tierArgs:
        tierArgs = eg.multenterbox("""What is the name and position of the new tier?
                    All Tiers:"""+str(tierids)+"""
                    Standard Tiers:"""+str(stdTiers), 
                    "Add Tier", ("Name","After"), ("Tier",""))
    print tierArgs
    
    for eafn in domain:
        eaf.insertTier(eaf.open(eafn),tierArgs[0],tierArgs[1])
    

def importTier():
    
    filename = eg.fileopenbox("Choose the file to import tiers from (TextGrid, FlexText, or SGM):",
                    "Choose a file",os.path.join(_WRK_DIR_,"*"))
    eg.msgbox("You chose: " + str(filename), "Survey Result")
   
def findClips():
    from src.process import timealign
    from src.formats import utfcsv

    clipnames = defineDomain("sound clip","wav")
    
    wavnames = defineDomain("long sound","wav")
            
    csvname = eg.filesavebox(title="Select a CSV destination file to save CSV data",
                             default=_WRK_DIR_+"index.csv")
    
    if clipnames and wavnames and csvname:
    
        csv = utfcsv.UnicodeWriter(csvname)
        csv.write(["Source","Clip","Annotation1","Annotation2","Annotation3","StartSec","StopSec","DurSec"])
        
        for clip in clipnames:
            for wav in wavnames:
                frames = timealign.getFrames(clip,wav)
                if frames:
                    print clip,"in",wav
                    annot = os.path.splitext(os.path.basename(clip))[0].replace("_"," ").split("-")
                    row = [os.path.basename(wav),os.path.basename(clip),
                           annot[0],''.join(annot[1:2]),'-'.join(annot[2:]),
                           frames[0]/float(frames[2]),frames[1]/float(frames[2]),
                           frames[1]/float(frames[2])-frames[0]/float(frames[2])]
                    csv.write([unicode(s) for s in row])
                    break
            
        csv.close()
        
    else:
        eg.msgbox("Action canceled because filenames not provided")

if __name__ == '__main__':
    
    wrk_dir = _WRK_DIR_
    
    while 1:
    
        msg ="""What do you want to do?
        Working Files: {wrk}
        """.format(wrk=wrk_dir[:30])
        title = u"Field Corpus-o-matic Manager"
        choices = ["Quit",
                   "Export to HTML", 
                   "Convert Transcriptions", 
                   "Change Tier Attributes", 
                   "Import Tiers",
                   "Find Clips in Sources"]
        chosen = eg.indexbox(msg, title, choices)
        
        if chosen:
            
            # note that we convert chosen to string, in case
            # the user cancelled the choice, and we got None.
            # eg.msgbox("You chose: " + unicode(choices[chosen]), "Survey Result")
            
            [exportHtml,convertTrans,changeAttr,importTier,findClips][chosen-1]()
        
        else:
            sys.exit(0)           # user chose Cancel