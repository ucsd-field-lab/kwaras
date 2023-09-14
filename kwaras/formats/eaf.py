# -*- coding: utf-8 -*-
"""
Created on Jul 27, 2012

@author: lucien
"""

from typing import Union, List, Optional
import os
import xml.etree.ElementTree as etree
from copy import deepcopy
import csv


class Eaf:
    def __init__(self, filename):

        if not filename.endswith(".eaf"):
            raise Exception("Not an EAF:" + filename)
        else:
            self.filename = filename
            # fstr = open(filename)
            # self.eafile = etree.fromstring('\n'.join(fstr))
            self.eafile = etree.parse(filename).getroot()
            self._init_times()

    def _init_times(self):
        timenodes = self.eafile.findall("TIME_ORDER/TIME_SLOT")
        stimes = {}
        prev = 0
        for tn in timenodes:
            now = int(tn.get("TIME_VALUE", default=prev + 1))  # default to one millisecond more
            stimes[tn.get("TIME_SLOT_ID")] = now
            prev = now

        aanodes = self.eafile.findall(".//ALIGNABLE_ANNOTATION")
        self.times = {}
        for aa in aanodes:
            self.times[aa.get("ANNOTATION_ID")] = [stimes[aa.get("TIME_SLOT_REF1")], stimes[aa.get("TIME_SLOT_REF2")]]
        self.times["ALL"] = (0, prev)

        ranodes = self.eafile.findall(".//REF_ANNOTATION")
        links = {}
        for ra in ranodes:
            links[ra.get("ANNOTATION_ID")] = ra.get("ANNOTATION_REF")
        for ra in ranodes:
            ra_id = ref = ra.get("ANNOTATION_ID")
            times = None
            for iter in range(5):
                ref = links.get(ref)
                if ref:
                    times = self.times.get(ref)
                    if times is not None:
                        break
            self.times[ra_id] = times

    def get_annotation(self, aref):
        """Get the annotation with the given ANNOTATION_ID"""
        anode = self.eafile.find("[@ANNOTATION_ID='{}']".format(aref))
        return anode

    def get_annotation_on(self, tid, node):
        """Get the annotation on tier @tid directly dependent on annotation @node"""
        aref = node.get("ANNOTATION_ID")
        tier = self.get_tier_by_id(tid)
        ranodes = tier.findall(".//REF_ANNOTATION")
        for ra in ranodes:
            if ra.get("ANNOTATION_REF") == aref:
                return ra

    def get_annotation_at(self, tid, time):
        """Get the annotation on tier @tid containing or starting at @time"""
        tier = self.get_tier_by_id(tid)
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

    def get_annotations_in(self, tid, start=0, stop=None):
        """Get a list of the annotations on tier @tid between @start and @stop, defaulting to all"""
        if stop is None:
            stop = self.times["ALL"][1]
        annots = []
        if tid in self.get_tier_ids():
            tier = self.get_tier_by_id(tid)
            aanodes = tier.findall(".//ALIGNABLE_ANNOTATION")
            if aanodes:
                # print "aanodes", len(aanodes)
                for aa in aanodes:
                    (ti, tf) = self.times[aa.get("ANNOTATION_ID")]
                    if start <= ti and tf <= stop:
                        annots.append(aa)
            else:
                ranodes = tier.findall(".//REF_ANNOTATION")
                # print "ranodes", len(ranodes)
                for ra in ranodes:
                    (ti, tf) = self.times[ra.get("ANNOTATION_REF")]
                    # print len(annots), [start, ti, tf, stop]
                    if (start <= ti) and (tf <= stop):
                        annots.append(ra)
        return annots

    def get_time(self, annot):
        """Get the (start, stop) times of the annotation @annot"""
        if annot.tag == "ALIGNABLE_ANNOTATION":
            ai = annot.get("ANNOTATION_ID")
            if ai not in self.times:
                print(ai)
            return self.times[ai]
        elif annot.tag == "REF_ANNOTATION":
            ar = annot.get("ANNOTATION_REF")
            if ar not in self.times:
                print(ar)
            return self.times[ar]
        elif annot.tag == "ANNOTATION":
            child = annot.findall("*")[0]
            return self.get_time(child)
        else:
            raise Exception("I can't find the time of a " + annot.tag)
            # need to create annotations for blank tiers

    def get_tier_ids(self):
        tiers = self.eafile.findall("TIER")
        ids = [t.get("TIER_ID") for t in tiers]
        return ids

    def get_tier_by_id(self, tid):
        tiers = self.eafile.findall("TIER")
        matchlist = [t for t in tiers if t.get("TIER_ID") == tid]
        if len(matchlist) == 1:
            targ = matchlist[0]
        elif len(matchlist) > 1:
            tierids = [t.get("TIER_ID") for t in tiers]
            sizes = [len(list(t)) for t in matchlist]
            targ = matchlist[sizes.index(max(sizes))]  # the largest tier
            print(("WARNING: TIER_ID {} matched {} nodes with lengths {}.\n{}"
                  .format(tid, len(matchlist), sizes, tierids)))
        else:
            tierids = [t.get("TIER_ID") for t in tiers]
            raise NameError("TIER_ID {} matched {} nodes.\n{}".format(tid, len(matchlist), tierids))
        return targ

    def insert_tier(self, tier, after=None):

        # make sure tid is not a duplicate
        tierids = self.get_tier_ids()
        tid = tier.get("TIER_ID")
        if tid in tierids:
            raise NameError("TIER_ID {} already used.".format(tid))

        # renumber the annotation ids appropriately
        lastIdElem = [prop for prop in self.eafile.findall("HEADER/PROPERTY")
                      if prop.get("NAME") == "lastUsedAnnotationId"][0]
        nextIdInt = int(lastIdElem.text) + 1

        annotes = list(tier.iter("ALIGNABLE_ANNOTATION")) + list(tier.iter("REF_ANNOTATION"))
        endIdInt = nextIdInt + len(annotes)

        for idx in range(nextIdInt, endIdInt):
            note = annotes.pop(0)
            note.set("ANNOTATION_ID", "a" + str(idx))
        lastIdElem.text = str(endIdInt - 1)

        # put it in the tree
        if after:  # not None and not blank
            at_idx = [k.get("TIER_ID", "") for k in self.eafile].index(after)
        else:
            # last tier
            at_idx = len(list(self.eafile.iter())) - list(reversed([k.tag for k in self.eafile.iter()])).index("TIER")

        self.eafile.insert(at_idx, tier)

        self._init_times()

    def copy_tier(self, src_id, targ_id, parent=None, ltype=None):

        srctier = self.get_tier_by_id(src_id)

        targ = deepcopy(srctier)
        targ.set("TIER_ID", targ_id)
        if parent is not None:
            targ.set("PARENT_REF", parent)
        if targ.get("PARENT_REF"):
            validtypes = self.get_valid_types(independent=False)
        else:
            validtypes = self.get_valid_types(independent=True)
        if ltype is not None:
            if ltype not in validtypes:
                raise RuntimeWarning("Type " + ltype + " is not recognized as a valid tier type.")
            targ.set("LINGUISTIC_TYPE_REF", ltype)
        self.rectify_type(targ)

        return targ

    def rename_tier(self, tier, new_id):

        old_id = tier.get("TIER_ID")
        tier.set("TIER_ID", new_id)
        deptiers = [t for t in self.eafile.iter("TIER") if t.get("PARENT_REF") == old_id]
        for dep in deptiers:
            dep.set("PARENT_REF", new_id)

    def change_parent(self, tier, new_ref, ltype=None):
        """Changes the parent and/or type of a tier. 
        @warning: changing the parentage or type can create an invalid eaf
        @todo: check that the parent and type are compatible"""
        if new_ref:
            tier.set("PARENT_REF", new_ref)
        else:
            if "PARENT_REF" in tier.attrib:
                del tier.attrib["PARENT_REF"]
        if ltype is not None:
            if ltype not in self.get_valid_types():
                raise RuntimeWarning(
                    "Type " + ltype + " is not recognized as a valid tier type:" + str(self.get_valid_types()))
            else:
                tier.set("LINGUISTIC_TYPE_REF", ltype)
        self.rectify_type(tier)

    def rectify_type(self, tier):
        """Ensure that the parentage, atype and time refs are appropriate to the tier's ltype"""
        parent = tier.get("PARENT_REF")
        ltype = tier.get("LINGUISTIC_TYPE_REF")
        ltype_node = self.eafile.find("LINGUISTIC_TYPE[@LINGUISTIC_TYPE_ID='{}']".format(ltype))
        if ltype_node.get("TIME_ALIGNABLE") == "true":
            refnotes = tier.findall("ANNOTATION/REF_ANNOTATION")
            if len(refnotes) > 0:
                print("REF_ANNOTATION in time-alignable tier", tier.get("TIER_ID"))
                for note in refnotes:
                    tref = self.get_time(note)
                    note.set("TIME_SLOT_REF1", tref[0])
                    note.set("TIME_SLOT_REF2", tref[1])
                    del note.attrib["ANNOTATION_REF"]
                    note.tag = "ALIGNABLE_ANNOTATION"
        else:
            alignnotes = tier.findall("ANNOTATION/ALIGNABLE_ANNOTATION")
            if len(alignnotes) > 0:
                print("ALIGNABLE_ANNOTATION in symbolic tier", tier.get("TIER_ID"))
                for note in alignnotes:
                    tref = self.get_time(note)
                    aref = self.get_annotation_at(parent, tref[0]).get("ANNOTATION_ID")
                    note.set("ANNOTATION_REF", aref)
                    del note.attrib["TIME_SLOT_REF1"]
                    del note.attrib["TIME_SLOT_REF2"]
                    note.tag = "REF_ANNOTATION"

    def get_valid_types(self, independent=None, time_alignable=None):

        types = self.eafile.findall("LINGUISTIC_TYPE")

        if independent is True:
            types = [lt for lt in types if lt.get("CONSTRAINTS") is None]
        elif independent is False:
            types = [lt for lt in types if lt.get("CONSTRAINTS") is not None]

        if time_alignable is None:
            types = [lt for lt in types]
        else:
            tas = str(time_alignable).lower()
            types = [lt for lt in types if lt.get("TIME_ALIGNABLE") == tas]

        typeids = [lt.get("LINGUISTIC_TYPE_ID") for lt in types]
        return typeids

    def import_types(self, template):
        """@template: filename of a .etf or .eaf with the types to be imported"""
        types = [lt.get("LINGUISTIC_TYPE_ID") for lt in self.eafile.findall("LINGUISTIC_TYPE")]

        fstr = open(template, encoding='utf8')
        etf = etree.fromstring('\n'.join(fstr))
        ltnodes = etf.findall("LINGUISTIC_TYPE")
        ltnodes = [lt for lt in ltnodes if lt.get("LINGUISTIC_TYPE_ID") not in types]

        end_to_last = list(reversed([k.tag for k in list(self.eafile)])).index("LINGUISTIC_TYPE")
        at_idx = len(list(self.eafile)) - end_to_last

        for lt in ltnodes:
            self.eafile.insert(at_idx, lt)

    # def importTiers(): maybe better to use ELAN's multiple edit

    def write(self, filename: Union[str, os.PathLike]):
        """Writes eaf to file at filename."""
        outstr = open(filename, 'w', encoding='utf-8')
        outstr.write(etree.tostring(self.eafile, encoding="unicode"))
        outstr.close()

    def status(self, fields: Optional[List[str]] = None) -> dict:
        """Report percent coverage of dependent tiers"""
        if fields is None:
            fnames = self.get_tier_ids()
        else:
            fnames = [f for f in self.get_tier_ids() if f.partition("@")[0] in fields]
        coverage = {}
        spkrs = set([f.partition("@")[2] for f in fnames])
        for spkr in spkrs:
            fset = [f for f in fnames if f.partition("@")[2] == spkr]
            baseline = fset[0]
            basenotes = self.get_annotations_in(baseline)
            for f in fset:
                count = 0
                if len(basenotes) > 0:
                    for bn in basenotes:
                        start, stop = self.get_time(bn)
                        fn = [n for n in self.get_annotations_in(f, start, stop)
                              if n.findtext("ANNOTATION_VALUE").strip() != '']
                        if len(fn) > 0:
                            count += 1
                    coverage[f] = round(float(count) / len(basenotes), 2)
                else:
                    coverage[f] = 0
        return coverage

    def export_to_csv(self,
        filename: Union[str, os.PathLike],
        dialect: str = 'excel',
        fields: Optional[List[str]] = None,
        mode: str= "w",
    ):
        """Duplicate the ELAN export function, with our settings and safe csv format
        @filename: path of new csv file
        @dialect: a csv.Dialect instance or the name of a registered Dialect
        @fields: list of fields to export (default exports all)
        @mode: fopen mode code ('w' to overwrite, 'a' to append)"""

        if fields is None:
            fnames = self.get_tier_ids()
        else:
            fnames = [f for f in self.get_tier_ids() if f.partition("@")[0] in fields]

        print("From", filename, "printing", fnames)
        columns = ("fieldname", "start", "end", "value", "filename")
        csvfile = csv.DictWriter(
            open(filename, mode, encoding='utf-8', newline=''), 
            dialect=dialect, 
            fieldnames=columns
        )
        if 'w' in mode:
            csvfile.writeheader()

        for f in fnames:
            annots = self.get_annotations_in(f)
            for a in annots:
                value = a.findtext("ANNOTATION_VALUE").strip()
                start, end = [str(t) for t in self.get_time(a)]
                row = {
                    "fieldname": f,
                    "start": start,
                    "end": end,
                    "value": value,
                    "filename": self.filename
                }
                csvfile.writerow(row)



if __name__ == '__main__':
    eaf = Eaf("/Users/lucien/Data/Raramuri/ELAN corpus/tx/tx1.eaf")

    eaf.export_to_csv("/Users/lucien/Data/Raramuri/ELAN corpus/tx1.csv")
