import glob
import re
from tqdm import tqdm
from lxml import etree

data_dir = "data/raw/2021-03-16-place-corr/"
results_dir = "data/processed/misc_corr/"

if __name__ == "__main__":
    # get all xml files
    xml_filenames = glob.glob("{}*.xml".format(data_dir))

    # correct misc stuff
    parser = etree.XMLParser(encoding="utf-8", recover=True, huge_tree=True, remove_blank_text=True)
    namespaces = {"tei": "http://www.tei-c.org/ns/1.0"}
    errors = []

    for fn in tqdm(xml_filenames, desc="processing files"):
        filename = fn.split("/")[-1]

        et = etree.parse(fn, parser)

        # remove old place normalizations
        try:
            place_norm_el = et.find("//tei:keywords[@scheme='cirilo:normalizedPlaceNames']...", namespaces=namespaces)
            place_norm_par = place_norm_el.find("..")
            place_norm_par.remove(place_norm_el)
        except AttributeError:
            pass

        # fix who attrib in revisions
        revision_el = et.find("//tei:revisionDesc", namespaces=namespaces)
        for i in revision_el.iterchildren():
            i.attrib["who"] = "#" + i.attrib["who"]

        # add new revision entries
        new_rev = etree.Element("change")
        new_rev.attrib["when"] = "2021-01"
        new_rev.attrib["who"] = "#MS #PK #SS"
        new_rev.text = "normalisation of person names"
        revision_el.append(new_rev)

        new_rev = etree.Element("change")
        new_rev.attrib["when"] = "2021-04"
        new_rev.attrib["who"] = "#MS #PK #SS"
        new_rev.text = "normalisation of place names"
        revision_el.append(new_rev)

        # change sanja resp
        try:
            sanja_el = et.find("//tei:name[@ref='https://orcid.org/0000-0002-0802-6999']", namespaces=namespaces)
            del sanja_el.attrib["ref"]
            sanja_par = sanja_el.find("..")
            sanja_par.attrib["ref"] = "https://orcid.org/0000-0002-0802-6999"
            sanja_par.attrib["{http://www.w3.org/XML/1998/namespace}id"] = "#SS"
            new_resp = etree.Element("resp")
            new_resp.text = "data correction"
            sanja_par.append(new_resp)
        except AttributeError:
            pass

        title_stmt_el = et.find("//tei:titleStmt", namespaces=namespaces)
        
        # add cg resp
        new_respStmt = etree.Element("respStmt")
        new_respStmt.attrib["{http://www.w3.org/XML/1998/namespace}id"] = "#CG"
        new_name = etree.Element("name")
        new_name.text = "Christina Glatz"
        new_respStmt.append(new_name)
        new_resp = etree.Element("resp")
        new_resp.text = "data correction"
        new_respStmt.append(new_resp)
        title_stmt_el.append(new_respStmt)

        # add pk resp
        new_respStmt = etree.Element("respStmt")
        new_respStmt.attrib["ref"] = "https://orcid.org/0000-0001-5492-0644"
        new_respStmt.attrib["{http://www.w3.org/XML/1998/namespace}id"] = "#PK"
        new_name = etree.Element("name")
        new_name.text = "Philipp Koncar"
        new_respStmt.append(new_name)
        new_resp = etree.Element("resp")
        new_resp.text = "data correction"
        new_respStmt.append(new_resp)
        title_stmt_el.append(new_respStmt)

        et.write("{}{}".format(results_dir, filename), pretty_print=True, xml_declaration=True, encoding="utf-8")
    
    print("done")
