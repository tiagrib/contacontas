# Copyright (c) 2022 Tiago Ribeiro
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from etl import pdf_etl as pdf
from report_sources.activobank import ActivoBank
from report_sources.paypal import PayPal
from data.contas_data import ContasData
import numpy as np
import csv
from time import perf_counter

class ContaContas:
    def __init__(self):
        self.sources = []
        self.banks = {}
        self.data = ContasData()

    def loadPDF(self, source):
        src = pdf.load(source)
        self.sources.append(src)
        self.parseSource(src)
    
    def loadCSV(self, source):
        if "paypal" in source.lower():
            src = []
            with open(source) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=';')
                for row in csv_reader:
                    src.append(row)
            self.sources.append(src)
            self.parseSource(src)

    def parseSource(self, src):
        if ActivoBank.is_source(src):
            print("Report source: ActivoBank.")
            activo = ActivoBank()
            if 'ActivoBank' not in self.banks:
                self.banks['ActivoBank'] = activo
            activo.parse_source(src)
        elif PayPal.is_source(src):
            print("Report source: PayPal CSV.")
            paypal = PayPal()
            if 'PayPal' not in self.banks:
                self.banks['PayPal'] = paypal
            paypal.parse_source(src)
        else:
            print("Failed to identify the source of the report.")

    def _count_prealloc(self):
        mov_count = 0
        acc_count = 0
        for bank in self.banks.values():
            for account in bank.accounts.values():
                acc_count += 1
                for segment in account.segments:
                    mov_count += len(segment.movements)
        return len(self.banks), acc_count, mov_count
        
    def digest(self):
        t1_start = perf_counter()
        print("Prepare DB...")
        self.data.prepare(*self._count_prealloc())
        print("Load DB...")
        for bank in self.banks.values():
            for account in bank.accounts.values():
                for segment in account.segments:
                    for mov in segment.movements:
                        self.data.record(bank.name, account.name, mov.date, mov.value, mov.desc)
        print("Finalize DB...")
        self.data.finalize()
        t1_stop = perf_counter()
        print("DB Digestion took:", t1_stop-t1_start)
        


    def launchGUI(self, gui):
        w = gui()
        return w.run(self)



    



