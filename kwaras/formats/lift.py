# -*- coding: utf-8 -*-
"""
Created on Apr 16, 2013

@author: lucien
"""

import xml.etree.ElementTree as eTree
from datetime import datetime
from copy import deepcopy

_LANG_CODE = ("en", "es")[0]

_SFM_TAGS_ = {
    "lexical-unit": "lx",
    "citation": "lc",
    "grammatical-info": "ps",
    "note": "co",
    "variant": "va",
    "pronunciation": "",
    "gloss": "g",
    "example": "x"
}

_EAFL_TAGS_ = {
    "lexical-unit": "Lexeme",
    "grammatical-info": "Pos",
    "variant": "Variant",
    "gloss": "Gloss",
}


class Lift:
    def __init__(self, filename):
        self.tree = eTree.parse(filename)
        self.root = self.tree.getroot()
        self.lexemes = {}
        entries = self.root.findall("entry")
        print(self.root.tag, len(entries))
        for node in entries:
            lx = node.find("lexical-unit/form/text").text
            eid = node.get("id")
            hm = 1
            key = (lx, hm)
            while key in self.lexemes:
                hm += 1
                key = (lx, hm)
            self.lexemes[key] = eid

    # def toSFM(self,filename):

    def getEntry(self, guid):
        """Look up a lexical entry by guid/eid.
        Given either the guid or eid, the lookup is based on guid."""
        guid = guid.split("_")[-1]
        entry = self.root.find("entry[@guid='{}']".format(guid))
        return entry

    def getPrimary(self, guid):
        """Get the main (primary) entry for a variant (secondary) entry"""
        entry = self.getEntry(guid)
        primary = None
        var_rel = entry.find("relation/trait[@name='variant-type']/..")
        if var_rel is not None:
            ref = var_rel.get("ref")
            primary = self.getEntry(ref)
        return primary

    def getField(self, guid, field):
        """Get attribute @attr node (XPATH) of entry that has unique id @guid"""
        entry = self.getEntry(guid)
        attrs = entry.findall(field)
        attrs += entry.findall("field[@type='{}']".format(field))
        if len(attrs) < 1:
            attr_node = None
        elif len(attrs) > 1:
            # print "Multiple instances of attribute", attr
            attr_node = attrs[0]
        else:
            attr_node = attrs[0]
        return attr_node

    def getPOS(self, guid):
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

    def getSenses(self, guid):

        entry = self.getEntry(guid)
        sns = entry.findall("sense")
        primary = self.getPrimary(guid)
        if len(sns) == 0 and primary is not None:
            sns = primary.findall("sense")
        return sns

    def getVarForms(self, guid):
        """Get a list of variant forms (allomorphs + pronunciations)"""
        frame = {"stem": "{}",
                 "prefix": "{}-",
                 "suffix": "-{}",
                 "proclitic": "{}=",
                 "enclitic": "={}",
                 "phrase": "{}"}
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

    def deleteVariant(self, guid, varform):
        entry = self.getEntry(guid)
        variants = entry.findall("variant")
        forms = [va.find("form/text") for va in variants]
        var = variants[forms.index(varform)]
        entry.remove(var)
        entry.set("dateModified", datetime.utcnow().isoformat().split(".")[0] + "Z")

    def appendVariant(self, guid, varform):
        entry = self.getEntry(guid)
        # print etree.tostring(entry)
        form = deepcopy(entry.find("lexical-unit/form"))
        form.find("text").text = varform
        trait = deepcopy(entry.find("trait[@name='morph-type']"))
        var = eTree.SubElement(entry, "variant")
        var.extend([form, trait])
        entry.set("dateModified", datetime.utcnow().isoformat().split(".")[0] + "Z")

    def setDateModified(self, guid, date=None):
        entry = self.getEntry(guid)
        if date is None:
            date = datetime.utcnow().isoformat().split(".")[0] + "Z"
        else:
            date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S").isoformat().split(".")[0] + "Z"
        entry.set("dateModified", date)

    def write(self, filename):
        self.tree.write(filename, 'utf-8', True)

    def toEAFL(self, filename, lang=_LANG_CODE):
        xml_wrapper = """
            <lexicon>
            </lexicon>"""
        le_xml = """
            <lexicalEntry id="{id}" dt="{dt}">
            <Lexeme typ="{mt}">{lx}</Lexeme>
                        <form />
                        <Pos>{ps}</Pos>
                </lexicalEntry>
                """
        sn_xml = """
                    <sense>
                        <stuff>
                        </stuff>
                        <Gloss lang="{lg}" tierX="{x}">{g}</Gloss>
                    </sense>
                    """
        af_xml = """
                    <altForm>
                        <WForm>{}</WForm>
                    </altForm>
                  """

        eafl = eTree.ElementTree(eTree.XML(xml_wrapper))
        lexicon = eafl.getroot()
        # print etree.tostring(lexicon), len(self.lexemes)
        lid = 1
        for lx, hm in self.lexemes:
            eid = self.lexemes[(lx, hm)]
            entry = self.getEntry(eid)

            # print "Working on:\n",etree.tostring(entry)

            psv = self.getPOS(eid)

            args = {
                "id": lid,
                "dt": entry.get("dateModified"),
                "mt": entry.find("trait[@name='morph-type']").get("value"),
                "lx": lx,
                "ps": psv
            }
            q = le_xml.format(**args)
            le = eTree.XML(q.encode("utf-8"))
            # print etree.tostring(le)

            # insert allomorphs
            variants = self.getVarForms(eid)
            for va in variants:
                if va not in ("", lx):
                    print({lx: va})
                    af = eTree.XML(af_xml.format(va).encode("utf-8"))
                    le.find("form").append(af)
                else:
                    print("Variant is lexeme form:", va)

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
                x = x + " (" + eid.split("_")[-1] + ")"
                if sense.find("gloss[@lang='{}']/text".format(lang)) is not None:
                    g = sense.find("gloss[@lang='{}']/text".format(lang)).text
                else:
                    g = ""
                args = {
                    "lg": lang,
                    "x": x,
                    "g": g
                }
                sn = eTree.XML(sn_xml.format(**args).encode("utf-8"))
                # TODO: add <stuff>
                le.append(sn)
            lid += 1
            # print etree.tostring(le)
            lexicon.append(le)
        eafl.write(filename, 'utf-8', True)


if __name__ == "__main__":
    import sys
    import os

    dirname = os.path.dirname(sys.argv[-1])
    for fname in os.listdir(dirname):
        base, ext = os.path.splitext(fname)
        if ext == ".lift":
            print("Converting", fname)
            lift = Lift(os.path.join(dirname, fname))
            lift.toEAFL(os.path.join(dirname, base + "-import.eafl"))
        else:
            print("Not converting", fname, "with extension:", ext)
