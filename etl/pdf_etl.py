# Copyright (c) 2022 Tiago Ribeiro
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import os.path
import sys
import traceback

import PyPDF2

def extract_to_txt(file_in, file_out):
    try:
        pdffileobj=open(file_in,'rb')
        pdfreader=PyPDF2.PdfReader(pdffileobj)
        text = []
        for p in pdfreader.pages:
            text.append(p.extract_text())
        with open(file_out,"a") as f:
            f.writelines(text)
    except:
        print("Failed to parse the PDF file:")
        traceback.print_exc(file=sys.stdout)


def load(file):
    try:
        if os.path.exists(file):
            if not os.path.exists(file + ".txt"):
                print("Extracting PDF to PDF-TXT file", file)
                extract_to_txt(file, file+".txt")
            file = file + ".txt"
        
            if os.path.exists(file):
                print("Loading PDF-TXT file", file)
                with open(file, encoding="cp1252") as f:
                    all_lines = f.read().replace("  ",' ').splitlines()
                return all_lines
            else:
                print(f"File {file} does not exist!")
        else:
            print(f"File {file} does not exist!")
            return None
    except:
        print("Failed to parse the PDF-TXT file:")
        traceback.print_exc(file=sys.stdout)