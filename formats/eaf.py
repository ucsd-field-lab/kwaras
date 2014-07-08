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
            self._init_times()
            
    def _init_times(self):
        timenodes = self.eafile.findall("TIME_ORDER/TIME_SLOT")
        stimes = {}
        prev = 0
        for tn in timenodes:
            now = int(tn.get("TIME_VALUE",default=prev+1)) # default to one millisecond more
            stimes[tn.get("TIME_SLOT_ID")] = now
            prev = now
            
        aanodes = self.eafile.findall(".//ALIGNABLE_ANNOTATION")
        self.times = {}
        for aa in aanodes:
            self.times[aa.get("ANNOTATION_ID")] = [stimes[aa.get("TIME_SLOT_REF1")], stimes[aa.get("TIME_SLOT_REF2")]]
        self.times["ALL"] = (0, prev)
    
    def getAnnotation(self,aref):
        """Get the annotation with the given ANNOTATION_ID"""
        anode = self.eafile.find("[@ANNOTATION_ID='{}']".format(aref))
        return anode
    
    def getAnnotationOn(self,tid,node):
        """Get the annotation on tier @tid directly dependent on annotation @node"""
        aref = node.get("ANNOTATION_ID")
        tier = self.getTierById(tid)
        ranodes = tier.findall(".//REF_ANNOTATION")
        for ra in ranodes:
            if ra.get("ANNOTATION_REF") == aref:
                return ra
        
    def getAnnotationAt(self,tid,time):
        """Get the annotation on tier @tid containing or starting at @time"""
        tier = self.getTierById(tid)
        aanodes = tier.findall(".//ALIGNABLE_ANNOTATION")
        if aanodes:
            for aa in aanodes:
                (start, stop) = self.times[aa.get("ANNOTATION_ID")]
                if start <= time < stop:
                    return aa
        else:
            ranodes = tier.findall(".//REF_ANNOTATION")
            for ra in ranodes:
                (start, stop) = self.times[ra.get("ANNOTATION_REF")]
                if start <= time < stop:
                    return ra
    
    def getAnnotationsIn(self,tid,start=0,stop=None):
        """Get a list of the annotations on tier @tid between @start and @stop, defaulting to all"""
        if stop is None:
            stop = self.times["ALL"][1]
        annots = []
        if tid in self.getTierIds():
            tier = self.getTierById(tid)
            aanodes = tier.findall(".//ALIGNABLE_ANNOTATION")
            if aanodes:
                #print "aanodes", len(aanodes)
                for aa in aanodes:
                    (ti, tf) = self.times[aa.get("ANNOTATION_ID")]
                    if start <= ti and tf <= stop:
                        annots.append(aa)
            else:
                ranodes = tier.findall(".//REF_ANNOTATION")
                #print "ranodes", len(ranodes)
                for ra in ranodes:
                    (ti, tf) = self.times[ra.get("ANNOTATION_REF")]
                    #print len(annots), [start, ti, tf, stop]
                    if (start <= ti) and (tf <= stop):
                        annots.append(ra)
        return annots
    
    def getTime(self,annot):
        """Get the (start, stop) times of the annotation @annot"""
        if annot.tag == "ALIGNABLE_ANNOTATION":
            return self.times[annot.get("ANNOTATION_ID")]
        else: # REF_ANNOTATION
            return self.times[annot.get("ANNOTATION_REF")]
        # need to create annotations for blank tiers

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
        
        self._init_times()

    def copyTier(self, src_id, targ_id, parent=None, ltype=None):
        
        srctier = self.getTierById(src_id)
        
        targ = deepcopy(srctier)
        targ.set("TIER_ID",targ_id)
        if parent is not None:
            targ.set("PARENT_REF",parent)
        if targ.get("PARENT_REF"):
            validtypes = self.getValidTypes(independent=False)
        else:
            validtypes = self.getValidTypes(independent=True)
        if ltype is not None:
            if ltype not in validtypes:
                raise RuntimeWarning("Type "+ltype+" is not recognized as a valid tier type.")
            targ.set("LINGUISTIC_TYPE_REF",ltype)
        self.rectifyType(targ)
                    
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
            if ltype not in self.getValidTypes():
                raise RuntimeWarning("Type "+ltype+" is not recognized as a valid tier type:"+str(self.getValidTypes()))
            else:
                tier.set("LINGUISTIC_TYPE_REF", ltype)
        self.rectifyType(tier)

    def rectifyType(self, tier):
        """Ensure that the parentage, atype and time refs are appropriate to the tier's ltype"""
        parent = tier.get("PARENT_REF")
        ltype = tier.get("LINGUISTIC_TYPE_REF")
        ltype_node = self.eafile.find("LINGUISTIC_TYPE[@LINGUISTIC_TYPE_ID='{}']".format(ltype))
        if ltype_node.get("TIME_ALIGNABLE") == "true":
            refnotes = tier.findall("ANNOTATION/REF_ANNOTATION")
            if len(refnotes) > 0:
                print "REF_ANNOTATION in time-alignable tier",tier.get("TIER_ID")
                for note in refnotes:
                    tref = self.getTime(note)
                    note.set("TIME_SLOT_REF1",tref[0])
                    note.set("TIME_SLOT_REF2",tref[1])
                    del note.attrib["ANNOTATION_REF"]
                    note.tag = "ALIGNABLE_ANNOTATION"
        else:
            alignnotes = tier.findall("ANNOTATION/ALIGNABLE_ANNOTATION")
            if len(alignnotes) > 0:
                print "ALIGNABLE_ANNOTATION in symbolic tier",tier.get("TIER_ID")
                for note in alignnotes:
                    tref = self.getTime(note)
                    aref = self.getAnnotationAt(parent, tref[0]).get("ANNOTATION_ID")
                    note.set("ANNOTATION_REF",aref)
                    del note.attrib["TIME_SLOT_REF1"]
                    del note.attrib["TIME_SLOT_REF2"]
                    note.tag = "REF_ANNOTATION"
                    


    def getValidTypes(self, independent=None, time_alignable=None):
        
        types = self.eafile.findall("LINGUISTIC_TYPE")
        
        if independent == True:
            types = [lt for lt in types if lt.get("CONSTRAINTS") is None]
        elif independent == False:
            types = [lt for lt in types if lt.get("CONSTRAINTS") is not None]
            
        if time_alignable is None:
            types = [lt for lt in types]
        else:
            tas = str(time_alignable).lower()
            types = [lt for lt in types if lt.get("TIME_ALIGNABLE") == tas]
            
        typeids = [lt.get("LINGUISTIC_TYPE_ID") for lt in types]
        return typeids
            
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
        
    def status(self, fields=None):
        """Report percent coverage of dependent tiers"""
        if fields is None:
            fnames = self.getTierIds()
        else:
            fnames = [f for f in self.getTierIds() if f.partition("@")[0] in fields]
        coverage = {}
        spkrs = set([f.partition("@")[2] for f in fnames])
        for spkr in spkrs:
            fset = [f for f in fnames if f.partition("@")[2] == spkr]
            baseline = fset[0]
            basenotes = self.getAnnotationsIn(baseline)
            for f in fset:
                count = 0
                if len(basenotes) > 0:
                    for bn in basenotes:
                        start, stop = self.getTime(bn)
                        fn = [n for n in self.getAnnotationsIn(f, start, stop) 
                              if n.findtext("ANNOTATION_VALUE").strip() != '']
                        if len(fn) > 0:
                            count += 1
                    coverage[f] = round(float(count) / len(basenotes),2)
                else:
                    coverage[f] = 0
        return coverage
        
    def exportToCSV(self, filename, dialect='excel', fields=None, mode="wb"):
        """Duplicate the ELAN export function, with our settings and safe csv format
        @filename: path of new csv file
        @dialect: a csv.Dialect instance or the name of a registered Dialect
        @fields: list of fields to export (default exports all)
        @mode: fopen mode code ('wb' to overwrite, 'ab' to append)"""
        
        if fields is None:
            fnames = self.getTierIds()
        else:
            fnames = [f for f in self.getTierIds() if f.partition("@")[0] in fields]

        print "printing", fnames
        csvfile = utfcsv.UnicodeWriter(filename, dialect, mode=mode)

        for f in fnames:
            annots = self.getAnnotationsIn(f)
            #print "annots",len(annots)
            for a in annots:
                value = a.findtext("ANNOTATION_VALUE")
                at = [str(t) for t in self.getTime(a)]
                #print [f] + at + [value, self.filename]
                csvfile.write([f] + at + [value, self.filename])
#                
#        for t in tiers:
#            tid = t.get("TIER_ID")
#            aanodes = t.findall(".//ALIGNABLE_ANNOTATION")
#            for aa in aanodes:
#                value = aa.findtext("ANNOTATION_VALUE")
#                aid = aa.get("ANNOTATION_ID")
#                csvfile.write([tid] + aatimes[aid] + [value, self.filename])
#            ranodes = t.findall(".//REF_ANNOTATION")
#            for ra in ranodes:
#                value = ra.findtext("ANNOTATION_VALUE")
#                aid = ra.get("ANNOTATION_REF")
#                csvfile.write([tid] + aatimes[aid] + [value, self.filename])
#            
        csvfile.close()
                
if __name__ == '__main__':
    
    eaf = Eaf("/Users/lucien/Data/Raramuri/ELAN corpus/tx/tx1.eaf")
    
    eaf.exportToCSV("/Users/lucien/Data/Raramuri/ELAN corpus/tx1.csv")
                