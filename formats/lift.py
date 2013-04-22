# -*- coding: utf-8 -*-
'''
Created on Apr 16, 2013

@author: lucien
'''

import xml.etree.ElementTree as etree

_LANG_CODE = ("en","es")[0]

_SFM_TAGS_ = {
        "lexical-unit":"lx",
        "citation":"lc",
        "grammatical-info":"ps",
        "note":"co",
        "variant":"va",
        "pronunciation":"",
        "gloss":"g",
        "example":"x"
               }

_EAFL_TAGS_ = {
        "lexical-unit":"Lexeme",
        "grammatical-info":"Pos",
        "variant":"Variant",
        "gloss":"Gloss",
               }

class Lift:
    
    def __init__(self,filename):
        self.root = etree.parse(filename).getroot()
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
        
        eafl = etree.ElementTree(etree.XML(xml_wrapper))
        lexicon = eafl.getroot()
        print etree.tostring(lexicon), len(self.lexemes)
        lid = 1
        for lx, hm in self.lexemes:
            eid = self.lexemes[(lx,hm)]
            try:
                entry = self.root.find("entry[@id='{}']".format(eid))
            except:
                print "BAD:", repr(eid)
                guid = eid.split("_")[1]
                entry = self.root.find("entry[@guid='{}']".format(guid))
                
            print "Working on:\n",etree.tostring(entry)
            
            ## if this is a variant, fall back on main entry sense info
            primary = None
            var_rel = entry.find("relation/trait[@name='variant-type']/..")
            if var_rel:
                ref = var_rel.get("ref").split("_")[-1]
                primary = self.root.find("entry[@guid='{}']".format(ref))
            
            ps = entry.find("sense/grammatical-info")
            if ps is None:
                if primary is not None:
                    ps = primary.find("sense/grammatical-info")
            if ps is None:
                psv = ""
            else:
                psv = ps.get("value")

            args = {
                    "id":lid,
                    "dt":entry.get("dateModified"),
                    "mt":entry.find("trait[@name='morph-type']").get("value"),
                    "lx":lx,
                    "ps":psv
                    }
            q = le_xml.format(**args)
            le = etree.XML(q.encode("utf-8"))
            print etree.tostring(le)
                            
            # insert allomorphs
            variants = entry.findall("variant")
            for va in variants:
                text_node = va.find("form/text")
                if text_node is not None:
                    af = etree.XML(af_xml.format(text_node.text).encode("utf-8"))
                    le.find("form").append(af)
                else:
                    print "Variant without text:",etree.tostring(va)
                
            # insert senses
            sns = entry.findall("sense")
            if len(sns) == 0 and primary is not None:
                sns = primary.findall("sense")
            for sense in sns:
                if sense.find("grammatical-info") is not None:
                    x = sense.find("grammatical-info").get("value")
                else:
                    x = ""
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
            print etree.tostring(le)
            lexicon.append(le)
        eafl.write(filename,'utf-8',True)
        
if __name__ == "__main__":
    import sys, os
    dirname = os.path.dirname(sys.argv[-1])
    for f in os.listdir(dirname):
        base, ext = os.path.splitext(f)
        if ext == ".lift":
            print "Converting",f
            lift = Lift(os.path.join(dirname,f))
            lift.toEAFL(os.path.join(dirname, base+"-import.eafl"))
        else:
            print "Not converting",f,"with extension:",ext
