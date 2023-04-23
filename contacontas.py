# Copyright (c) 2022 Tiago Ribeiro
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from etl import pdf_etl as pdf
from report_sources.activobank import ActivoBank
from report_sources.paypal import PayPal
from data.contas_data import ContasData
from data.config import Config
import csv
from time import perf_counter

class ContaContas:
    def __init__(self):
        self.sources = []
        self.banks = {}
        self.data = ContasData()
        self.config = Config()


    def loadPDF(self, source):
        cache = self.config.get_source_cache(source)
        if cache is None:
            src = pdf.load(source)
            self.sources.append(src)
            self.config.save_source_cache(source, self.parseSource(src))
        else:
            self.reloadSourceCache(cache)
    
    def loadCSV(self, source):
        if "paypal" in source.lower():
            cache = self.config.get_source_cache(source)
            if cache is None:
                src = []
                with open(source) as csv_file:
                    csv_reader = csv.reader(csv_file, delimiter=';')
                    for row in csv_reader:
                        src.append(row)
                self.sources.append(src)
                self.config.save_source_cache(source, self.parseSource(src))
            else:
                self.reloadSourceCache(cache)

    def reloadSourceCache(self, data):
        if data:
            if isinstance(data, ActivoBank):
                self.banks['ActivoBank'] = data
            elif isinstance(data, PayPal):
                self.banks['PayPal'] = data
        
    def parseSource(self, src):
        if ActivoBank.is_source(src):
            print("Report source: ActivoBank.")
            activo = ActivoBank()
            if 'ActivoBank' not in self.banks:
                self.banks['ActivoBank'] = activo
            activo.parse_source(src)
            return activo
        elif PayPal.is_source(src):
            print("Report source: PayPal CSV.")
            paypal = PayPal()
            if 'PayPal' not in self.banks:
                self.banks['PayPal'] = paypal
            paypal.parse_source(src)
            return paypal
        else:
            print("Failed to identify the source of the report.")
            return None

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
        if not self.config.cocodb_cache or self.config.any_uncached_data_loaded:
            print("Rebuild DB...")
            self.data.prepare(*self._count_prealloc())
            print("Load DB...")
            for bank in self.banks.values():
                for account in bank.accounts.values():
                    for segment in account.segments:
                        for mov in segment.movements:
                            self.data.record(bank.name, account.name, mov.date, mov.value, mov.desc)
            print("Finalize DB...")
            self.data.finalize()
            self.config.save_cocodb(self.data)
        else:
            print("Load DB from cache...")
            self.data = self.config.load_cocodb()
            self.data.classify()

        t1_stop = perf_counter()
        print("DB Digestion took:", t1_stop-t1_start)
        


    def launchGUI(self, gui):
        w = gui()
        return w.run(self)



    



