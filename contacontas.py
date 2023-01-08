# Copyright (c) 2022 Tiago Ribeiro
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from etl import pdf_etl as pdf
from report_sources import activobank

class ContaContas:
    def __init__(self):
        self.sources = []
        self.banks = {}

    def loadPDF(self, source):
        src = pdf.load(source)
        self.sources.append(src)
        self.parseSource(src)

    def parseSource(self, src):
        # ActivoBank
        if activobank.is_activo_bank(src):
            print("Report source: ActivoBank.")
            activo = activobank.ActivoBank()
            if 'ActivoBank' not in self.banks:
                self.banks['ActivoBank'] = activo
            activo.activo_bank_parse_report(src)
        else:
            print("Failed to identify the source of the report.")

    def launchGUI(self, gui):
        w = gui(self)
        return w.run()



    



