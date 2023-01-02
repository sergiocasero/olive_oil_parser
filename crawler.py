# Create a script that crawls a website and returns a list of all the pdf links on the page.

import requests
from bs4 import BeautifulSoup
import os
import PyPDF2
import re
import json

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

    #convert to int
    return {
        "id" : int(tupleId),
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
            print(category["label"] + ": " +line)
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

        # add the value to the category.values array
        category["history"].append(tuple)


    pdfFileObj.close()
        

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

def test():
    extract_pdf_info("pdfs/512022boletinsemanalpreciosaceitedeoliva2021-22_tcm30-640308.pdf")
    with open("test.json", "w") as f:
        json.dump(categories, f, indent=4)
        f.close()

if __name__ == "__main__":
    crawl()
    # test()
    
    
        
    
