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
            aval = x.findtext("ANNOTATION_VALUE")
            print aval
            if aval is '':
                print "Blank X annotation:", eaf.etree.tostring(x)
                e = None
            else:
                gidm = re.search("\(([^.]*)\)",x.findtext("ANNOTATION_VALUE"))
                gid = gidm.group(1)
                print "gid:",gid
                e = eafl.getEntry(gid)
                
            if e is None:
                g = None
            else:   
                sns = eafl.getSenses(gid)
                sense = sns[0]
                g = sense.find("gloss[@lang='{}']/text".format(_LANG_CODE))       
                
            if g is None:
                gloss = eafile.getAnnotationOn(tiers['g'], m)
                gloss.find("ANNOTATION_VALUE").text = ""                 
            else:
                newg = g.text
                gloss = eafile.getAnnotationOn(tiers['g'], m)
                print gloss.find("ANNOTATION_VALUE").text, "=>", newg
                gloss.find("ANNOTATION_VALUE").text = newg
        
    return eafile

if __name__ == '__main__':
    
    testfile = r"C:\Users\Public\Documents\ELAN\texts\tx1.eaf"
    outfile = r"C:\Users\Public\Documents\ELAN\texts\tx1.eaf"
    lexicon = r"C:\Users\Public\Documents\ELAN\ELAN.lift"
    
    eafile = eaf.Eaf(testfile)
    eafl = liftadd.Lift(lexicon)
    tiernames = {"m":"Morph","g":"MGloss-ES","x":"MCat"}
    eafile = update(eafile, tiernames, eafl)
    eafile.write(testfile)
    