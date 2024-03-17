# Copyright (c) 2022 Tiago Ribeiro
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import os.path
import sys
import traceback

import PyPDF2


def save_lines_to_txt(filename, lines):
    for i, _ in enumerate(lines):
        lines[i] += "\n"
    with open(filename, "w", encoding='utf-8') as f:
        f.writelines(lines)


def extract_to_txt(file_in, file_out):
    try:
        pdffileobj=open(file_in,'rb')
        pdfreader=PyPDF2.PdfReader(pdffileobj, strict=True)
        text = []
        for p in pdfreader.pages:
            text.append(p.extract_text())
        save_lines_to_txt(file_out, text)
        print(f"Saved txt lines to '{file_out}'.")
    except:
        print("Failed to parse the PDF file:")
        traceback.print_exc(file=sys.stdout)


def load(file):
    file = str(file)
    try:
        if os.path.exists(file):
            if not os.path.exists(file + ".txt"):
                print("Extracting PDF to PDF-TXT file", file)
                extract_to_txt(file, file+".txt")
            file = file + ".txt"
        
            if os.path.exists(file):
                print("Loading PDF-TXT file", file)
                with open(file, encoding="utf-8") as f:
                    all_lines = f.read()
                    while '  ' in all_lines:
                        all_lines = all_lines.replace('  ', ' ')
                    all_lines = all_lines.splitlines()
                    loaded_n = len(all_lines)
                    all_lines = [s.strip() for s in all_lines if s.strip() != '']
                    if loaded_n != len(all_lines):
                        save_lines_to_txt(file, all_lines.copy())
                        print(f"Saved clean txt lines to '{file}'.")

                return all_lines
            else:
                print(f"File {file} does not exist!")
        else:
            print(f"File {file} does not exist!")
            return None
    except:
        print("Failed to parse the PDF-TXT file:")
        traceback.print_exc(file=sys.stdout)