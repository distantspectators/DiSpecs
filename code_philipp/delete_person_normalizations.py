import pandas as pd
import re
from tqdm import tqdm
from lxml import etree

data_dir = "data/raw/2021-05-05/"
results_dir = "data/processed/norm_corr/"

if __name__ == "__main__":
    corrected_normalizations = pd.read_csv("data/normalization/persons_corr.csv")
    corrected_normalizations.fillna("", inplace=True)

    normalizations_to_delete = corrected_normalizations[corrected_normalizations["note"] == "DELETE"]

    # correct normalizations
    parser = etree.XMLParser(encoding="utf-8", recover=True, huge_tree=True)
    namespaces = {"tei": "http://www.tei-c.org/ns/1.0"}
    errors = []
    for fn, rows in tqdm(normalizations_to_delete.groupby("filename")):
        try:
            et = etree.parse("{}{}".format(data_dir, fn), parser)
        except OSError:
            errors.append("{}: file not found!".format(fn))
            continue

        for row_idx, row in rows.iterrows():
            elements = et.xpath("//tei:persName[@xml:id='{}']".format(row["id"]), namespaces=namespaces)
            
            # sanity checks
            try:
                assert len(elements) == 1
            except AssertionError:
                errors.append("{}: multiple elements with id {}".format(fn, row["id"]))
                continue
            el = elements[0]
            
            pre_el = el.getprevious()
            par_el = el.find("..")

            print(fn, row["id"])

            try:
                if pre_el.tail is None:
                    pre_el.tail = ""
                pre_el.tail += el.text
                if el.tail is not None:
                    pre_el.tail += el.tail
            except AttributeError:
                if par_el.text is None:
                    par_el.text = ""
                par_el.text += el.text
                par_el.text += el.tail
            

            par_el.remove(el)

        et.write("{}{}".format(results_dir, fn), pretty_print=True, xml_declaration=True, encoding="utf-8")

    print("done")
