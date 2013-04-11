# -*- coding: utf-8 -*-
'''
Created on Jul 27, 2012

@author: lucien
'''

import utfcsv
import xml.etree.ElementTree as etree
from copy import deepcopy

class Eaf:
    
    def __init__(self,filename):

        if not filename.endswith(".eaf"):
            raise Exception("Not an EAF:"+filename)
        else:
            self.filename = filename
            #fstr = open(filename)
            #self.eafile = etree.fromstring('\n'.join(fstr))
            self.eafile = etree.parse(filename).getroot()

    def getTierIds(self):
        tiers = self.eafile.findall("TIER")
        ids = [t.get("TIER_ID") for t in tiers]
        return ids

    def getTierById(self,tid):
        tiers = self.eafile.findall("TIER")
        matchlist = [t for t in tiers if t.get("TIER_ID") == tid]
        if len(matchlist) == 1:
            targ = matchlist[0]
        elif len(matchlist) > 1:
            tierids = [t.get("TIER_ID") for t in tiers]
            sizes = [len(list(t)) for t in matchlist]
            targ = matchlist[sizes.index(max(sizes))] # the largest tier
            print("WARNING: TIER_ID {} matched {} nodes with lengths {}.\n{}".format(tid,len(matchlist),sizes,tierids))
        else:
            tierids = [t.get("TIER_ID") for t in tiers]
            raise NameError("TIER_ID {} matched {} nodes.\n{}".format(tid,len(matchlist),tierids))
        return targ
    
    def getAnnotation(self,time):
        pass
    
    def getTime(self,note):
        pass
        # need to create annotations for blank tiers
    
    def insertTier(self,tier,after=None):
        
        # make sure tid is not a duplicate
        tierids = self.getTierIds()
        tid = tier.get("TIER_ID")
        if tid in tierids:
            raise NameError("TIER_ID {} already used.".format(tid))
        
        # renumber the annotation ids appropriately
        lastIdElem = [prop for prop in self.eafile.findall("HEADER/PROPERTY") 
                      if prop.get("NAME") == "lastUsedAnnotationId"][0]
        nextIdInt = int(lastIdElem.text)+1
                
        annotes = list(tier.iter("ALIGNABLE_ANNOTATION")) + list(tier.iter("REF_ANNOTATION"))
        endIdInt = nextIdInt+len(annotes)
        
        for idx in range(nextIdInt,endIdInt):
            note = annotes.pop(0)
            note.set("ANNOTATION_ID","a"+str(idx))
        lastIdElem.text = str(endIdInt-1)    
        
        # put it in the tree
        if after: # not None and not blank
            at_idx = [k.get("TIER_ID","") for k in self.eafile].index(after)
        else:
            # last tier
            at_idx = len(list(self.eafile.iter())) - list(reversed([k.tag for k in self.eafile.iter()])).index("TIER")
            
        self.eafile.insert(at_idx,tier)

    def copyTier(self, src_id, targ_id, parent=None, ltype=None):
        
        srctier = self.getTierById(src_id)
        
        targ = deepcopy(srctier)
        targ.set("TIER_ID",targ_id)
        if parent is not None:
            targ.set("PARENT_REF",parent)
        if targ.get("PARENT_REF"):
            validtypes = self.getValidTypes(time_alignable=False)
        else:
            validtypes = self.getValidTypes(time_alignable=True)
        if ltype is not None:
            if ltype not in validtypes:
                raise RuntimeWarning("Type "+ltype+" is not recognized as a valid tier type.")
            targ.set("LINGUISTIC_TYPE_REF",ltype)
                    
        return targ
        
    def renameTier(self, tier, new_id):
        
        old_id = tier.get("TIER_ID")
        tier.set("TIER_ID", new_id)
        deptiers = [t for t in self.eafile.iter("TIER") if t.get("PARENT_REF") == old_id]
        for dep in deptiers:
            dep.set("PARENT_REF", new_id)
            
    def changeParent(self, tier, new_ref, ltype=None):
        """Changes the parent and/or type of a tier. 
        @warning: changing the parentage or type can create an invalid eaf
        @todo: check that the parent and type are compatible"""
        if new_ref:
            tier.set("PARENT_REF", new_ref)
        else:
            if "PARENT_REF" in tier.attrib:
                del tier.attrib["PARENT_REF"]
        if ltype is not None:
            tier.set("LINGUISTIC_TYPE_REF", ltype)
        

    def getValidTypes(self, time_alignable=None):
        
        types = self.eafile.findall("LINGUISTIC_TYPE")
        if time_alignable is None:
            types = [lt.get("LINGUISTIC_TYPE_ID") for lt in types]
        else:
            tas = str(time_alignable).lower()
            types = [lt.get("LINGUISTIC_TYPE_ID") for lt in types if lt.get("TIME_ALIGNABLE") == tas]
        return types
            
    def importTypes(self, template):
        """@template: filename of a .etf or .eaf with the types to be imported"""
        types = [lt.get("LINGUISTIC_TYPE_ID") for lt in self.eafile.findall("LINGUISTIC_TYPE")]

        fstr = open(template)
        etf = etree.fromstring('\n'.join(fstr))
        ltnodes = etf.findall("LINGUISTIC_TYPE")
        ltnodes = [lt for lt in ltnodes if lt.get("LINGUISTIC_TYPE_ID") not in types]
        
        end_to_last = list(reversed([k.tag for k in list(self.eafile)])).index("LINGUISTIC_TYPE")
        at_idx = len(list(self.eafile)) - end_to_last
        
        for lt in ltnodes:
            self.eafile.insert(at_idx, lt)
        
    # def importTiers(): maybe better to use ELAN's multiple edit
    
    def write(self, filename):
        outstr = open(filename, 'wb')
        outstr.write(etree.tostring(self.eafile, encoding="UTF-8"))
        outstr.close()
        
    def exportToCSV(self, filename, dialect='excel', fields=None, mode="wb"):
        """Duplicate the ELAN export function, with our settings and safe csv format
        @filename: path of new csv file
        @dialect: a csv.Dialect instance or the name of a registered Dialect
        @fields: list of fields to export (default exports all)
        @mode: fopen mode code ('wb' to overwrite, 'ab' to append)"""
        
        tiers = self.eafile.findall("TIER")
        if fields:
            tiers = [t for t in tiers if t.get("TIER_ID") in fields]
        else:
            fields = self.getTierIds()
                
        timenodes = self.eafile.findall("TIME_ORDER/TIME_SLOT")
        times = {}
        prev = 0
        for tn in timenodes:
            now = tn.get("TIME_VALUE",default=str(prev+1)) # default to one millisecond more
            times[tn.get("TIME_SLOT_ID")] = now
            prev = int(now)
            
        aanodes = self.eafile.findall(".//ALIGNABLE_ANNOTATION")
        aatimes = {}
        for aa in aanodes:
            aatimes[aa.get("ANNOTATION_ID")] = [times[aa.get("TIME_SLOT_REF1")], times[aa.get("TIME_SLOT_REF2")]]
                    
        csvfile = utfcsv.UnicodeWriter(filename, dialect, mode=mode)

        for t in tiers:
            tid = t.get("TIER_ID")
            aanodes = t.findall(".//ALIGNABLE_ANNOTATION")
            for aa in aanodes:
                value = aa.findtext("ANNOTATION_VALUE")
                aid = aa.get("ANNOTATION_ID")
                csvfile.write([tid] + aatimes[aid] + [value, self.filename])
            ranodes = t.findall(".//REF_ANNOTATION")
            for ra in ranodes:
                value = ra.findtext("ANNOTATION_VALUE")
                aid = ra.get("ANNOTATION_REF")
                csvfile.write([tid] + aatimes[aid] + [value, self.filename])
            
        csvfile.close()
                
if __name__ == '__main__':
    
    eaf = Eaf("/Users/lucien/Data/Raramuri/ELAN corpus/tx/tx1.eaf")
    
    eaf.exportToCSV("/Users/lucien/Data/Raramuri/ELAN corpus/tx1.csv")
                