# -*- coding: utf-8 -*-
'''
Created on Apr 16, 2013

@author: lucien
'''

import xml.etree.ElementTree as etree
from datetime import datetime
from copy import deepcopy
import re

_LANG_CODE = ("en","es")[0]

##_SFM_TAGS_ = {
##        "lexical-unit":"lx",
##        "citation":"lc",
##        "grammatical-info":"ps",
##        "note":"co",
##        "variant":"va",
##        "pronunciation":"",
##        "gloss":"g",
##        "example":"x"
##               }
##
##_EAFL_TAGS_ = {
##        "lexical-unit":"Lexeme",
##        "grammatical-info":"Pos",
##        "variant":"Variant",
##        "gloss":"Gloss",
##               }

class Lift:
    
    def __init__(self,filename):
        self.tree = etree.parse(filename)
        self.root = self.tree.getroot()
        self.lexemes = {}
        entries = self.root.findall("entry")
        print self.root.tag, len(entries)
        for node in entries:
            lx = node.find("lexical-unit/form/text").text
            eid = node.get("id")
            hm = 1
            key = (lx, hm)
            while key in self.lexemes:
                hm = hm + 1
                key = (lx, hm)
            self.lexemes[key] = eid
    
    #def toSFM(self,filename):

    def getEntry(self,guid):
        """Look up a lexical entry by guid/eid.
        Given either the guid or eid, the lookup is based on guid."""
        guid = guid.split("_")[-1]
        entry = self.root.find("entry[@guid='{}']".format(guid))
        return entry

    def getPrimary(self,guid):
        """Get the main (primary) entry for a variant (secondary) entry"""
        entry = self.getEntry(guid)
        primary = None
        var_rel = entry.find("relation/trait[@name='variant-type']/..")
        if var_rel is not None:
            ref = var_rel.get("ref")
            primary = self.getEntry(ref)
        return primary

    def getPOS(self,guid):
        """Get the POS value, from the entry itself if available,
        otherwise from the primary entry for a variant entry."""
        entry = self.getEntry(guid)
        ps = entry.find("sense/grammatical-info")
        if ps is None:
            primary = self.getPrimary(guid)
            if primary is not None:
                ps = primary.find("sense/grammatical-info")
                
        if ps is None:
            psv = ""
        else:
            psv = ps.get("value")
        return psv

    def getSenses(self,guid):

        entry = self.getEntry(guid)
        sns = entry.findall("sense")
        primary = self.getPrimary(guid)
        if len(sns) == 0 and primary is not None:
            sns = primary.findall("sense")
        return sns

##    def getVariants(self,guid):
##        """Get a list of variant subentries (i.e. allomorphs)"""
##        entry = self.getEntry(guid)        
##        variants = entry.findall("variant")
##        forms = [va.find("form/text") for va in variants]              
##        return [f for f in forms if f is not None]

    def getVarForms(self,guid):
        """Get a list of variant forms (allomorphs + pronunciations)"""
        frame = {"stem":u"{}",
                 "prefix":u"{}-",
                 "suffix":u"-{}",
                 "proclitic":u"{}=",
                 "enclitic":u"={}",
                 "phrase":u"{}"}
        entry = self.getEntry(guid)
        mtype = entry.find("trait[@name='morph-type']").get("value")
        
        forms = [va.find("form/text")
                 for va in entry.findall("variant")]
        vtexts = [f.text for f in forms if f is not None]
        forms = [va.find("form/text")
                  for va in entry.findall("pronunciation")]
        ptexts = [frame[mtype].format(f.text)
                 for f in forms if f is not None]
                               
        return vtexts + ptexts      

    def deleteVariant(self,guid,varform):
        entry = self.getEntry(guid)
        variants = entry.findall("variant")
        forms = [va.find("form/text") for va in variants]
        var = variants[forms.index(varform)]
        entry.remove(var)
        entry.set("dateModified",datetime.utcnow().isoformat().split(".")[0]+"Z")

    def appendVariant(self,guid,varform):
        entry = self.getEntry(guid)
        #print etree.tostring(entry)
        form = deepcopy(entry.find("lexical-unit/form"))
        form.find("text").text = varform 
        trait = deepcopy(entry.find("trait[@name='morph-type']"))
        var = etree.SubElement(entry,"variant")
        var.extend([form,trait])
        entry.set("dateModified",datetime.utcnow().isoformat().split(".")[0]+"Z")

    def write(self,filename):
        self.tree.write(filename,'utf-8',True)

    def toEAFL(self,filename):
        xml_wrapper = u"""
            <lexicon>
            </lexicon>"""
        le_xml = u"""
            <lexicalEntry id="{id}" dt="{dt}">
            <Lexeme typ="{mt}">{lx}</Lexeme>
                        <form />
                        <Pos>{ps}</Pos>
                </lexicalEntry>
                """
        sn_xml = u"""
                    <sense>
                        <stuff>
                        </stuff>
                        <Gloss lang="{lg}" tierX="{x}">{g}</Gloss>
                    </sense>
                    """
        af_xml = u"""
                    <altForm>
                        <WForm>{}</WForm>
                    </altForm>
                  """
        #parser = etree.XMLParser(encoding="utf-8")
        
        eafl = etree.ElementTree(etree.XML(xml_wrapper))
        lexicon = eafl.getroot()
        #print etree.tostring(lexicon), len(self.lexemes)
        lid = 1
        for lx, hm in self.lexemes:
            eid = self.lexemes[(lx,hm)]
            entry = self.getEntry(eid)

            #print "Working on:\n",etree.tostring(entry)

            psv = self.getPOS(eid)

            args = {
                    "id":lid,
                    "dt":entry.get("dateModified"),
                    "mt":entry.find("trait[@name='morph-type']").get("value"),
                    "lx":lx,
                    "ps":psv
                    }
            q = le_xml.format(**args)
            le = etree.XML(q.encode("utf-8"))
            #print etree.tostring(le)
                            
            # insert allomorphs
            variants = self.getVarForms(eid)
            for va in variants:
                if va not in ("", lx):
                    print {lx:va}
                    af = etree.XML(af_xml.format(va).encode("utf-8"))
                    le.find("form").append(af)
                  
##            variants = entry.findall("variant")
##            for va in variants:
##                text_node = va.find("form/text")
##                if text_node is not None:
##                    af = etree.XML(af_xml.format(text_node.text).encode("utf-8"))
##                    le.find("form").append(af)
##                #else:
##                    #print "Variant without text:",etree.tostring(va)

            # insert senses
            sns = self.getSenses(eid)
            for sense in sns:
                ps = sense.find("grammatical-info")
                if ps is not None:
                    x = ps.get("value")
                    traits = ps.findall("trait")
                    x = ": ".join([x] + [t.get("value") for t in traits])
                else:
                    x = "NA"
                x = x + " ("+eid.split("_")[-1]+")"
                if sense.find("gloss[@lang='{}']/text".format(_LANG_CODE)) is not None:
                    g = sense.find("gloss[@lang='{}']/text".format(_LANG_CODE)).text
                else:
                    g = ""
                args = {
                        "lg":_LANG_CODE,
                        "x":x,
                        "g":g
                        }
                sn = etree.XML(sn_xml.format(**args).encode("utf-8"))
                # TODO: add <stuff>
                le.append(sn)
            lid += 1
            #print etree.tostring(le)
            lexicon.append(le)
        eafl.write(filename,'utf-8',True)



def addRarAllomorphs(infile,outfile):
    _V_ = u"aeiouɪɛəɔʊ"
    
    lift = Lift(infile)
    for lex, eid in lift.lexemes.items():
        # get list of forms (pronunciations plus allomorphs)
        forms = lift.getVarForms(eid)
        #print forms

        newforms = []
        # for any monosyllabic forms, suggest forms with and without stress
        for f in forms:
            m = re.search(u"^[^"+_V_+"]*["+_V_+"][^"+_V_+"]*$",f)
            if m:
                nostress = re.sub(u"ˈ","",f)
                sep = re.match(u"([-=]?)(.*)",nostress)
                wstress = sep.group(1) + u"ˈ" + sep.group(2)
                newforms += [nostress, wstress]
                
        # for any suggested forms not already in the list of forms, add them
        newforms = [f for f in newforms if f not in forms]
        print "forms:",forms,"newforms:",newforms
        for f in newforms:
            lift.appendVariant(eid,f)
        forms += newforms
        

        newforms = []
        # for any forms that have /r/ or /l/, suggest [ɾ]
        for f in forms:
            m = re.search(u"r",f)
            if m:
                newforms += [re.sub(u"r",u"ɾ",f)]
            m = re.search(u"l",f)
            if m:
                newforms += [re.sub(u"l",u"ɾ",f)]
                
        # for any suggested forms not already in the list of forms, add them
        newforms = [f for f in newforms if f not in forms]
        for f in newforms:
            lift.appendVariant(eid,f)
        forms += newforms

        newforms = []
        # for any forms that have /ʃ/ (but not /tʃ/), suggest /s/
        for f in forms:
            m = re.search(u"^ʃ",f)
            if m:
                newforms += [re.sub(u"^ʃ","s",f)]
            m = re.search(u"(?<!t)ʃ",f)
            if m:
                newforms += [re.sub(u"(?<!t)ʃ","s",f)]

        # for any forms that have /s/ before /u/ or /i/, suggest /ʃ/
        for f in forms:
            m = re.search(u"s[iu]",f)
            if m:
                newforms += [re.sub(u"s(?=[iu])",u"ʃ",f)]
                
        # for any suggested forms not already in the list of forms, add them
        newforms = [f for f in newforms if f not in forms]
        for f in newforms:
            lift.appendVariant(eid,f)
        forms += newforms

        newforms = []
        # for any forms that have final stress, suggest forms with long vowels
        for f in forms:
            m = re.search(u"ˈ[^{V}]*([{V}])$".format(V=_V_),f)
            if m:
                #print f, m.group()
                newforms += [f+m.group(1)]
            #else:
                #print f, "no match"
        # for any forms that have penultimate stress, suggest deleted vowels
        for f in forms:
            m = re.search(u"ˈ[^{V}]*[{V}][^{V}][ʃ]?([{V}])$".format(V=_V_),f)
            if m:
                #print f, m.group()
                newforms += [f[:-1]]
            #else:
                #print f, "no match"
                
        # for any suggested forms not already in the list of forms, add them
        #print newforms
        newforms = [f for f in newforms if f not in forms]
        for f in newforms:
            lift.appendVariant(eid,f)
        
    # dump the lift data to a new file
    lift.write(outfile)
        
if __name__ == "__main__":
    import sys, os
    dirname = os.path.dirname(sys.argv[-1])
    for f in os.listdir(dirname):
        base, ext = os.path.splitext(f)
        if ext == ".lift":
            print "Converting",f
            addRarAllomorphs(os.path.join(dirname,f),
                            os.path.join(dirname,"added.xml"))
            lift = Lift(os.path.join(dirname,"added.xml"))
            lift.toEAFL(os.path.join(dirname, base+"-import.eafl"))

        else:
            print "Not converting",f,"with extension:",ext
