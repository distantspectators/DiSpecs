import glob
import pandas as pd
import re
from tqdm import tqdm
from lxml import etree

data_dir = "data/raw/2021-05-07/"
results_dir = "data/processed/"
errors = []

def_nde = {
    None: None,
    "E1": 1,
    "E2": 2,
    "E3": 3,
    "E4": 4,
    "E5": 5,
    "E6": 6
}

def_ndf = {
    None: None,
    "AE": "Allgemeine Erzählung",
    "SP": "Selbstportrait",
    "FP": "Fremdportrait",
    "D": "Dialog",
    "AL": "Allegorisches Erzählen",
    "TR": "Traumerzählung",
    "F": "Fabelerzählung",
    "S": "Satirisches Erzählen",
    "EX": "Exemplarisches Erzählen",
    "UT": "Utopische Erzählung",
    "MT": "Metatextualität",
    "ZM": "Zitat/Motto",
    "LB": "Leserbrief"
}

def error_report(filename,  message, linenumber=None):
    if linenumber is None:
        errors.append("[{}] {}".format(filename, message))
    else:
        errors.append("[{}] {} (on line {})".format(filename, message, linenumber))

if __name__ == "__main__":
    xml_filenames = glob.glob("{}*.xml".format(data_dir))
    parser = etree.XMLParser(encoding="utf-8", recover=True, huge_tree=True)
    namespaces = {"tei": "http://www.tei-c.org/ns/1.0"}
    
    extracted_files = []

    for fn in tqdm(xml_filenames, desc="processing files"):
        filename = fn.split("/")[-1]

        et = etree.parse(fn, parser)
        text_element = et.xpath("//tei:text", namespaces=namespaces)[0]

        #journal title
        try:
            periodical_title_element = et.xpath("//tei:sourceDesc/tei:bibl/tei:title ", namespaces=namespaces)[0]
            periodical_title_text = periodical_title_element.text.strip().replace("\n", " ")
            periodical_title_text = re.sub(r"\s+", " ", periodical_title_text)
        except IndexError:
            periodical_title = "missing"
            error_report(filename, "periodical title element missing")
        except AttributeError:
            periodical_title = "missing"
            error_report(filename, "periodical title text missing", periodical_title_element.sourceline)

        # volume number
        try:
            volume_number_element = et.xpath("//tei:sourceDesc/tei:bibl/tei:biblScope[contains(@unit, 'vol')]", namespaces=namespaces)[0]
            volume_number_text = volume_number_element.text.strip()
        except IndexError:
            volume_number_text = "missing"
            error_report(filename, "volume number element missing")
        except AttributeError:
            volume_number_text = "missing"
            error_report(filename, "volume number text missing", volume_number_element.sourceline)

        # issue number
        try:
            issue_number_element = et.xpath("//tei:sourceDesc/tei:bibl/tei:biblScope[@unit='issue']", namespaces=namespaces)[0]
            issue_number_text = issue_number_element.text.strip()
        except IndexError:
            issue_number_text = "missing"
            error_report(filename, "issue number element missing")
        except AttributeError:
            issue_number_text = "missing"
            error_report(filename, "issue number text missing", issue_number_element.sourceline)

        # issue title
        try:
            issue_title_element = et.xpath("//tei:titleStmt/tei:title", namespaces=namespaces)[0]
            issue_title_text = issue_title_element.text.strip()
        except IndexError:
            issue_title_text = "missing"
            error_report(filename, "issue title element missing")
        except AttributeError:
            issue_title_text = "missing"
            error_report(filename, "issue title text missing", issue_title_element.sourceline)
            
        # author
        try:
            author_element = et.xpath("//tei:titleStmt/tei:author", namespaces=namespaces)[0]
            author_text = author_element.text.strip()
            author_text = re.sub(r"\s+", " ", author_text)
            if author_text in ["Anónimo", "Anonymus"]:
                author_text = "Anonym"
        except IndexError:
            author_text = "missing"
            error_report(filename, "author element missing")
        except AttributeError:
            author_text = "missing"
            error_report(filename, "author text missing", author_element.sourceline)
        
        # country
        try:
            country_element = et.xpath("//tei:sourceDesc/tei:bibl/tei:placeName", namespaces=namespaces)[0]
            country_text = country_element.text.strip()
        except IndexError:
            country_text = "missing"
            error_report(filename, "country element missing")
        except AttributeError:
            country_text = "missing"
            error_report(filename, "country text missing", country_element.sourceline)
        
        # language
        try:
            language_element = et.xpath("//tei:profileDesc/tei:langUsage/tei:language", namespaces=namespaces)[0]
            language_text = language_element.text.strip()
        except IndexError:
            language_text = "missing"
            error_report(filename, "language element missing")
        except AttributeError:
            language_text = "missing"
            error_report(filename, "language text missing", language_element.sourceline)
        
        # date
        try:
            date_element = et.xpath("//tei:sourceDesc/tei:bibl/tei:date", namespaces=namespaces)[0]
            date_text = date_element.text.strip()
        except IndexError:
            date_text = "missing"
            error_report(filename, "date element missing")
        except AttributeError:
            date_text = "missing"
            error_report(filename, "date text missing", date_element.sourceline)
        
        # topics
        topics = set()
        for t in et.xpath("//tei:profileDesc/tei:textClass/tei:keywords/tei:term/tei:term[@xml:lang='en']", namespaces=namespaces):
            topics.add(re.sub(r"\s+", " ", t.text).strip())
        if len(topics) == 0:
            error_report(filename, "topics missing")

        file_attributes = {
            "filename": filename,
            "periodical_title": periodical_title_text,
            "volume_number": volume_number_text,
            "issue_number": issue_number_text,
            "issue_title": issue_title_text,
            "author": author_text,
            "country": country_text,
            "language": language_text,
            "date": date_text,
            "topics": topics,
        }

        # text element
        nde_queue = [""]
        ndf_queue = [""]
        anchors_mapping = {}
        text_passages = []
        text = ""
        position = 0
        persons = set()
        places = set()
        works = set()
        text_buffer = []

        for c in text_element.iterdescendants():
            tag = c.tag.replace("{http://www.tei-c.org/ns/1.0}", "")

            # handle buffer
            pass_tail = False
            for tb in text_buffer:
                tb[1] = tb[1] - 1
                if tb[1] == 0:
                    text += tb[0]
            text_buffer = [tb for tb in text_buffer if tb[1] > 0]

            if tag == "milestone":
                text = re.sub(r"\s\s+", " ", text.replace("\n", " ")).strip()
                if text != "":
                    text_passages.append({"position": position, "level": nde_queue[-1], "form": ndf_queue[-1], "text": text, "persons": persons, "places": places, "works": works})
                    text = ""
                    position += 1
                    persons = set()
                    places = set()
                    works = set()
                unit = c.attrib["unit"]
                ana = c.attrib["ana"].split(" ")
                spanTo = c.attrib["spanTo"].replace("#", "")
                if unit == "level":
                    level = def_nde[ana[0].replace("#", "")]
                    nde_queue.append(level)
                    anchors_mapping[spanTo] = level
                elif unit == "form":
                    form = def_ndf[ana[0].replace("#", "")]
                    ndf_queue.append(form)
                    anchors_mapping[spanTo] = form

            if tag == "anchor":
                text = re.sub(r"\s\s+", " ", text.replace("\n", " ")).strip()
                if text != "":
                    text_passages.append({"position": position, "level": nde_queue[-1], "form": ndf_queue[-1], "text": text, "persons": persons, "places": places, "works": works})
                    text = ""
                    position += 1
                    persons = set()
                    places = set()
                    works = set()
                anchor = c.attrib["{http://www.w3.org/XML/1998/namespace}id"]
                try:
                    if anchors_mapping[anchor] == nde_queue[-1]:
                        nde_queue.pop()
                    elif anchors_mapping[anchor] == ndf_queue[-1]:
                        ndf_queue.pop()
                except KeyError:
                    error_report(filename, "missing anchor(s)")
            
            # persons
            if tag == "persName":
                try:
                    person_ref = c.attrib["ref"]
                    persons.add(person_ref)
                except KeyError:
                    error_report(filename, "person normalization missing", c.sourceline)

            # places
            if tag == "placeName":
                try:
                    place_ref = c.attrib["ref"]
                    places.add(place_ref)
                except KeyError:
                    error_report(filename, "place normalization missing", c.sourceline)

            # works
            if tag == "name":
                if c.attrib["type"] == "work":
                    try:
                        work_ref = c.attrib["ref"]
                        works.add(work_ref)
                    except KeyError:
                        error_report(filename, "work normalization missing", c.sourceline)

            # insert space for paragraphs, list labels, list items, notes, linebreaks, headlines
            if tag in ["p", "label", "item", "note", "lb", "head", "l"]:
                text += " "

            # remove - to connect words
            if tag == "pc":
                c.text = ""

            if tag in ["hi", "note", "persName", "placeName", "name"] and len(list(c)) > 0:
                if c.tail:
                    text_buffer.insert(0, [c.tail, len(list(c.iterdescendants())) + 1])
                    pass_tail = True

            if tag not in ["list", "milestone", "anchor", "pb", "lb"]:
                try:
                    text += c.text
                except TypeError:
                    pass

            if tag not in ["p", "head", "div", "list", "label", "item", "lg", "l"] and not pass_tail:
                try:
                    text += c.tail
                except TypeError:
                    pass

        try:
            assert len(nde_queue) == 1
        except AssertionError:
            error_report(filename, "missing anchor(s)")

        try:
            assert len(ndf_queue) == 1
        except AssertionError:
            error_report(filename, "missing anchor(s)")

        for tp in text_passages:
            tp.update(file_attributes)
        extracted_files.append(pd.DataFrame(text_passages))

    extracted_files_df = pd.concat(extracted_files)

    print("saving data frame")
    extracted_files_df.to_pickle("{}texts_new.p".format(results_dir))
    
    print("saving error report")
    with open("{}error_report.txt".format(results_dir), mode="wt", encoding='utf-8') as error_file:
        error_file.write("\n".join(errors))
