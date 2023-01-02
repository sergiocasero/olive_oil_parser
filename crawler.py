# Create a script that crawls a website and returns a list of all the pdf links on the page.

import requests
from bs4 import BeautifulSoup
import os
import PyPDF2
import re
import json
import datetime

endpoint = "https://www.mapa.gob.es"
url = endpoint + "/es/agricultura/temas/producciones-agricolas/aceite-oliva-y-aceituna-mesa/Evolucion_precios_AO_vegetales.aspx"

categories = [
    { "id": "aove", "label": "Aceite de oliva virgen extra", "history": [] },
    { "id": "aov", "label": "Aceite de oliva virgen", "history": [] },
    { "id": "aol", "label": "Aceite de oliva lampante", "history": [] },
    { "id": "aof", "label": "Aceite de oliva refinado", "history": [] },
    { "id": "aouor", "label": "Aceite de orujo de oliva refinado", "history": [] },
    { "id": "mso", "label": "MEDIA SIN ORUJO", "history": [] }
]

def get_pdf_links(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    pdf_links = []
    for link in soup.find_all("a"):
        href = link.get("href")
        if href.endswith(".pdf") and not href.endswith("cookies.pdf"):
            pdf_links.append(endpoint + link.get("href"))
    return pdf_links

def save_pdf(pdf_link):
    response = requests.get(pdf_link)
    filename = "pdfs/" + pdf_link.split("/")[-1]

    with open(filename, "wb") as f:
        f.write(response.content)
        f.close()

def save_pdfs(newPdfs, localPdfs):
    # check if pdf is already downloaded
    for pdf in newPdfs:
        pdfName = pdf.split("/")[-1]
        if "pdfs/" + pdfName not in localPdfs:
            print("should save " + pdfName)
            save_pdf(pdf)

def getLocalPdfs():
    pdfs = []
    for pdf in os.listdir("pdfs"):
        pdfs.append("pdfs/" + pdf)
    return pdfs

def extract_tuple_id(filename):
    # extract the tuple id from the filename string
    # the id is the first 6 characters of the filename
    id = filename.split("_")[0].split("/")[-1][:6]

    # get the first 2 characters of the id, and the last 4
    # the first 2 characters are the week, the last 4 are the year
    week = id[:2]
    year = id[2:]

    tupleId = year + week

    # get the datetime from week number and year
    d = year + "-W" + week

    r = datetime.datetime.strptime(d + '-1', "%Y-W%W-%w")

    #convert to int
    return {
        "id" : int(tupleId),
        "datetime": r.strftime("%Y-%m-%d"),
        "label": "Semana " + week + " de " + year,
        "value": 0
    }

def extractCategoryLine(page, category):
    text = page.extract_text()
    
    # split text by lines
    lines = text.split("\n")

    # find the line that contains the category text, reverse the list and iterate until we find the next category
    lines.reverse()
    for line in lines:
        line = line.replace("**", "")
        if line.startswith(category["label"]):
            line = line.replace(category["label"], "")
            return line.strip().split(" ")[1]

def extract_pdf_info(pdf):
    # we need to extract tables from pdf
    pdfFileObj = open(pdf, "rb")
    pdfReader = PyPDF2.PdfReader(pdfFileObj)

    # get the category
    for category in categories:
        # get the tuple id
        tuple = extract_tuple_id(pdf)
        value = extractCategoryLine(pdfReader.pages[1], category)

        # add the value to the category, parse to float
        tuple["value"] = float(value.replace(",", "."))
        tuple["ccaa"] = extract_ccaas_history(category["id"], pdfReader.pages[5])

        # add the value to the category.values array
        category["history"].append(tuple)

    

    pdfFileObj.close()


def extract_ccaa_info(lines, ccaa):
    ccaaTuples = []
    for line in lines:
        if line.startswith(ccaa):
            tuple = line.split(" ")
            valuePosition = 5
            if ccaa == "Castilla-La Mancha":
                valuePosition = 6
            tuple = tuple[valuePosition].replace(",", ".")
            tuple = float(tuple)

            ccaaTuples.append(tuple)
    return ccaaTuples

def extract_ccaas_history(categoryId, page):
    text = page.extract_text()
    lines = text.split("\n")
    
    valueToExtract = 0
    if categoryId == "aove":
        valueToExtract = 0
    elif categoryId == "aov":
        valueToExtract = 1
    elif categoryId == "aol":
        valueToExtract = 2

    result = {
        "andalucia": extract_ccaa_info(lines, "Andalucía")[valueToExtract],
        "catalunya": extract_ccaa_info(lines, "Cataluña")[valueToExtract],
        "extremadura": extract_ccaa_info(lines, "Extremadura")[valueToExtract]
    }

    if valueToExtract == 0 or valueToExtract == 1:
        result["castillaLaMancha"] = extract_ccaa_info(lines, "Castilla-La Mancha")[valueToExtract]
    
    return result


def crawl():
    pdfs = get_pdf_links(url)
    save_pdfs(pdfs, getLocalPdfs())

    savedPdfs = getLocalPdfs()

    for pdf in savedPdfs:
        try:
            extract_pdf_info(pdf)
        except Exception as e:
            print(e)
            print("Error extracting info from " + pdf)
            continue

    for category in categories:
        # sort the history array by id
        category["history"].sort(key=lambda x: x["id"])

    # save categories to json
    with open("data.json", "w") as f:
        json.dump(categories, f, indent=4)
        f.close()

    # now, create a csv file per category
    separator = ";"
    for category in categories:
        with open(category["id"] + ".csv", "w") as f:
            f.write("id;datetime;label;spain;andalucia;catalunya;castillaLaMancha;extremadura")
            f.write("\n")
            for tuple in category["history"]:
                cm = 0
                # if  tuple["ccaa"]["castillaLaMancha"] exists, add it to the cm variable



                if "castillaLaMancha" in tuple["ccaa"]:
                    cm = tuple["ccaa"]["castillaLaMancha"]
                f.write(str(tuple["id"]) + separator + tuple["datetime"] + separator + tuple["label"] + separator + str(tuple["value"]) + separator + str(tuple["ccaa"]["andalucia"]) + separator + str(tuple["ccaa"]["catalunya"]) + separator + str(cm) + separator + str(tuple["ccaa"]["extremadura"]))
                f.write("\n")

            f.close()


def test():
    extract_pdf_info("pdfs/512022boletinsemanalpreciosaceitedeoliva2021-22_tcm30-640308.pdf")
    with open("test.json", "w") as f:
        json.dump(categories, f, indent=4)
        f.close()

if __name__ == "__main__":
    crawl()
    # test()
    
    
        
    
