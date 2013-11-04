'''
Created on Nov 3, 2013

@author: lscarrol
'''
from formats import eaf, liftadd
import re

_LANG_CODE = ("en","es")[1]

def update(eafile,tiers,eafl):
    
    for m in eafile.getAnnotationsIn(tiers["m"]):
        x = eafile.getAnnotationOn(tiers["x"], m)
        if x is not None:
            gidm = re.search("\(([^.]*)\)",x.findtext("ANNOTATION_VALUE"))
            gid = gidm.group(1)
            print gid, x.findtext("ANNOTATION_VALUE")
            e = eafl.getEntry(gid)
            if e is not None:
                sns = eafl.getSenses(gid)
                sense = sns[0]
                if sense.find("gloss[@lang='{}']/text".format(_LANG_CODE)) is not None:
                    newg = sense.find("gloss[@lang='{}']/text".format(_LANG_CODE)).text
                    g = eafile.getAnnotationOn(tiers['g'], m)
                    print g.find("ANNOTATION_VALUE").text, newg
                    g.find("ANNOTATION_VALUE").text = newg
                else:
                    g = eafile.getAnnotationOn(tiers['g'], m)
                    g.find("ANNOTATION_VALUE").text = ""                    
            else:
                g = eafile.getAnnotationOn(tiers['g'], m)
                g.find("ANNOTATION_VALUE").text = ""
        
    return eafile

if __name__ == '__main__':
    
    testfile = r"C:\Users\Public\Documents\ELAN\texts\tx12.eaf"
    outfile = r"C:\Users\Public\Documents\ELAN\texts\tx12.eaf"
    lexicon = r"C:\Users\Public\Documents\ELAN\ELAN.lift"
    
    eafile = eaf.Eaf(testfile)
    eafl = liftadd.Lift(lexicon)
    tiernames = {"m":"Morph","g":"MGloss-ES","x":"MCat"}
    eafile = update(eafile, tiernames, eafl)
    eafile.write(testfile)
    