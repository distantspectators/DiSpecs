import pandas as pd
import re
from tqdm import tqdm
from lxml import etree

data_dir = "data/raw/2020-12-22/"
results_dir = "data/processed/norm_corr/"

if __name__ == "__main__":
    corrected_normalizations = pd.read_csv("data/normalization/persons_corr.csv")
    corrected_normalizations.fillna("", inplace=True)

    # creating unique reference ids
    unique_idx = corrected_normalizations.groupby(["normalization", "wikidataURL", "type"]).size().index
    unique_ids = {}
    unique_ids_raw = []
    for ide, idx in enumerate(unique_idx):
        unique_ids[idx] = "pers:P.{:04d}".format(ide)
        unique_ids_raw.append({"unique_id": "pers:P.{:04d}".format(ide), "normalization": idx[0], "wikidataURL": idx[1], "type": idx[2]})

    # saving them to csv
    pd.DataFrame(unique_ids_raw).to_csv("data/processed/unique_person_ids.csv", index=False)

    # correct normalizations
    parser = etree.XMLParser(encoding="utf-8", recover=True, huge_tree=True)
    namespaces = {"tei": "http://www.tei-c.org/ns/1.0"}
    errors = []
    for fn, rows in tqdm(corrected_normalizations.groupby("filename")):
        try:
            et = etree.parse("{}{}".format(data_dir, fn), parser)
        except OSError:
            errors.append("{}: file not found!".format(fn))
            continue

        try:
            assert len(rows) == len(et.xpath("//tei:persName", namespaces=namespaces))
        except AssertionError:
            errors.append("{}: unknown persName tag {}".format(fn, row["id"]))

        for row_idx, row in rows.iterrows():
            elements = et.xpath("//tei:persName[@xml:id='{}']".format(row["id"]), namespaces=namespaces)
            
            # sanity checks
            try:
                assert len(elements) == 1
            except AssertionError:
                errors.append("{}: multiple elements with id {}".format(fn, row["id"]))
                continue
            el = elements[0]
            
            try:
                assert re.sub(r"\s\s+", " ", el.text).strip().replace("\n", "") == row["text"].replace("\n", " ").strip()
            except AssertionError:
                errors.append("{}: text deviation for id {} (expected {} but found {})".format(fn, row["id"], row["text"], el.text))
                #continue
            except AttributeError:
                errors.append("{}: text deviation for id {} (expected {} but found '')".format(fn, row["id"], row["text"]))
                #continue
            except TypeError:
                errors.append("{}: text deviation for id {} (no string found)".format(fn, row["id"], row["text"]))
                #continue

            # all good
            el.attrib["ref"] = unique_ids[(row["normalization"], row["wikidataURL"], row["type"])]
            del el.attrib["type"]

        et.write("{}{}".format(results_dir, fn), pretty_print=True, xml_declaration=True, encoding="utf-8")
        #break
    
    # save errors
    pd.Series(errors).to_csv("data/processed/normalization_errors.csv", index=False, header=False)
    
    print("done")
