# -*- coding: utf-8 -*-
'''
Created on Jul 27, 2012

@author: lucien
'''

import xml.etree.ElementTree as etree
from copy import deepcopy

def open(filename):
    if not filename.endswith(".eaf"):
        raise Exception(' '.join(["Not an EAF:",filename]))
    else:
        fstr = open(filename)
        eafile = etree.fromstring('\n'.join(fstr))
    return eafile

def getTierIds(eafile):
    tiers = eafile.findall("TIER")
    ids = [t.get("TIER_ID") for t in tiers]
    return ids

def getTierById(eafile, tid):
    tiers = eafile.findall("TIER")
    matchlist = [t for t in tiers if t.get("TIER_ID") == tid]
    if len(matchlist) == 1:
        targ = matchlist[0]
    else:
        raise NameError("TIER_ID matched {} nodes.".format(len(matchlist)))
    return targ

def insertTier(eaf,tier,after=None):
    lastIdElem = [prop for prop in eaf.findall("HEADER/PROPERTY") if prop.get("NAME") == "lastUsedAnnotationId"][0]
    nextIdInt = int(lastIdElem.text)+1
            
    annotes = list(tier.iter("ALIGNABLE_ANNOTATION")) + list(tier.iter("REF_ANNOTATION"))
    endIdInt = nextIdInt+len(annotes)
    
    for idx in range(nextIdInt,endIdInt):
        note = annotes.pop(0)
        note.set("ANNOTATION_ID","a"+str(idx))
    lastIdElem.text = str(endIdInt-1)    
    
    if after: # not None and not blank
        at_idx = [k.get("TIER_ID","") for k in eaf].index(after.get("TIER_ID"))
    else:
        # last tier
        at_idx = len(list(eaf.iter())) - list(reversed([k.tag for k in eaf.iter()])).index("TIER")
    eaf.insert(at_idx,tier)


def copyTier(srctier,targ_id,parent=None,ltype=None):
    
    targ = deepcopy(srctier)
    targ.set("TIER_ID",targ_id)
    if parent is not None:
        targ.set("PARENT_REF",parent)
    if ltype is not None:
        targ.set("LINGUISTIC_TYPE_REF",ltype)
                
    return targ
    
def renameTier(tier,new_id,eaf):
    
    old_id = tier.get("TIER_ID")
    tier.set("TIER_ID", new_id)
    deptiers = [t for t in eaf.iter("TIER") if t.get("PARENT_REF") == old_id]
    for dep in deptiers:
        dep.set("PARENT_REF", new_id)

            