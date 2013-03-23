# -*- coding: utf-8 -*-
'''
Created on Jul 27, 2012

@author: lucien
'''

import xml.etree.ElementTree as etree
from copy import deepcopy

def load(filename):
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
        tids = list(set( [t.get("TIER_ID") for t in tiers] ))
        raise NameError("TIER_ID {} matched {} nodes.\n{}".format(tid,len(matchlist),tids))
    return targ

def insertTier(eaf,tier,after=None):
    lastIdElem = [prop for prop in eaf.findall("HEADER/PROPERTY") 
                  if prop.get("NAME") == "lastUsedAnnotationId"][0]
    nextIdInt = int(lastIdElem.text)+1
            
    annotes = list(tier.iter("ALIGNABLE_ANNOTATION")) + list(tier.iter("REF_ANNOTATION"))
    endIdInt = nextIdInt+len(annotes)
    
    for idx in range(nextIdInt,endIdInt):
        note = annotes.pop(0)
        note.set("ANNOTATION_ID","a"+str(idx))
    lastIdElem.text = str(endIdInt-1)    
    
    if after: # not None and not blank
        at_idx = [k.get("TIER_ID","") for k in eaf].index(after)
    else:
        # last tier
        at_idx = len(list(eaf.iter())) - list(reversed([k.tag for k in eaf.iter()])).index("TIER")
    eaf.insert(at_idx,tier)


def copyTier(eaf, src_id, targ_id, parent=None, ltype=None):
    
    srctier = getTierById(eaf, src_id)
    
    targ = deepcopy(srctier)
    targ.set("TIER_ID",targ_id)
    if parent is not None:
        targ.set("PARENT_REF",parent)
    if targ.get("PARENT_REF"):
        validtypes = getValidTypes(eaf, time_alignable=False)
    else:
        validtypes = getValidTypes(eaf, time_alignable=True)
    if ltype is not None:
        if ltype not in validtypes:
            raise RuntimeWarning("Type "+ltype+" is not recognized as a valid tier type.")
        targ.set("LINGUISTIC_TYPE_REF",ltype)
                
    return targ
    
def renameTier(tier,new_id,eaf):
    
    old_id = tier.get("TIER_ID")
    tier.set("TIER_ID", new_id)
    deptiers = [t for t in eaf.iter("TIER") if t.get("PARENT_REF") == old_id]
    for dep in deptiers:
        dep.set("PARENT_REF", new_id)

def getValidTypes(eaf, time_alignable=None):
    
    types = eaf.findall("LINGUISTIC_TYPE")
    if time_alignable is None:
        types = [lt.get("LINGUISTIC_TYPE_ID") for lt in types]
    else:
        tas = str(time_alignable).lower()
        types = [lt.get("LINGUISTIC_TYPE_ID") for lt in types if lt.get("TIME_ALIGNABLE") == tas]
    return types
        
        
        