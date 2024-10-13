# Copyright (c) 2022 Tiago Ribeiro
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from pathlib import Path
import pickle
from data.bank import Account, Bank
from data.overviews import Overviews
from etl import pdf_etl as pdf
from report_sources.activobank import ActivoBank
from report_sources.paypal import PayPal
from data.numpandas_database import NumpandasDatabase
from data.config import Config
import csv
import argparse
from datetime import datetime
import pandas as pd

STORAGE_FILE = "cc.pkl"


class ContaContas:
    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-r", "--rebuild", help="Rebuild the cache on load.", action="store_true")
        self.ccargs = parser.parse_args()
        if Path(STORAGE_FILE).exists() and not self.ccargs.rebuild:
            self.reload(parser)
        else:
            self.init(parser)
        self.months = []

    def init(self, parser):
        self.ccargs = parser.parse_args()
        self.sources = []
        self.banks = {}
        self.data = NumpandasDatabase()
        self.clustering = {"kmeans": {"clusters": 0, "names": [], "idxs": []}}
        self.autoclasses = {}
        self.classes = {}
        self.config = Config(self.ccargs)
        self.over = Overviews(self)
        self.load_sources_from_config()

    def get_bank_accounts(self):
        res = []
        for bank in self.banks.values():
            for account in bank.accounts.values():
                res.append(bank.name + "." + account.name)
        return res

    def load_sources_from_config(self):
        self.init_manual_sources()

        self.init_unsored_sources()

        self.finalize_loading()

    def init_unsored_sources(self):
        for path in self.config.setup["unsorted_source_paths"]:
            pathfiles = Path(path).glob("**/*")
            for file in pathfiles:
                if file.suffix.lower() == ".csv":
                    self.loadCSV(file)
                elif file.suffix.lower() == ".pdf":
                    self.loadPDF(file)

    def init_manual_sources(self):
        for bank_name, binfo in self.config.setup["banks"].items():
            bank_name = bank_name.lower()
            if bank_name in self.banks:
                bank = self.banks[bank_name]
            else:
                bank = None
                if bank_name in ["activobank", "paypal"]:
                    bank = {"activobank": ActivoBank(), "paypal": PayPal()}[bank_name]
                else:
                    print(f"Invalid bank name '{bank_name}' in config!.")
            if bank and "accounts" in binfo:
                for account_name, info in binfo["accounts"].items():
                    if info is None or info == {}:
                        print(f"Failed to initialize account '{account_name}' from config! Invalid info '{info}'.")
                    else:
                        print(f"Initialize account '{account_name}' from bank '{bank_name}'.")
                        account = Account(bank=bank, account_name=account_name, initial_value=info["initial_value"] if "initial_value" in info else False, all_internal=info["all_internal"] if "all_internal" in info else False)
                        bank.add_account(account)
                self.digest_source(bank)

    def reload(self, parser):
        with open(STORAGE_FILE, "rb") as file:
            storage = pickle.load(file)
            self.__dict__.update(storage.__dict__)
        print(f"Reload storage from '{STORAGE_FILE}'")
        self.ccargs = parser.parse_args()
        self.config = Config(self.ccargs)

    def save(self):
        with open(STORAGE_FILE, "wb") as file:
            pickle.dump(self, file)
        self.config.save()
        print(f"Saved storage to '{STORAGE_FILE}'")

    def loadPDF(self, source):
        if self.config.rebuild_cache:
            cache = None
        else:
            cache = self.config.get_source_cache(source)
        if cache is None:
            src = pdf.load(source)
            self.sources.append(src)
            self.config.save_source_cache(source, self.digest_source(src))
        elif self.config.reload_data:
            self.digest_source(cache)

    def loadCSV(self, source):
        source = str(source)
        if "paypal" in source.lower():
            if self.config.rebuild_cache:
                cache = None
            else:
                cache = self.config.get_source_cache(source)
            if cache is None:
                src = []
                with open(source, encoding="utf-8") as csv_file:
                    csv_reader = csv.reader(csv_file, delimiter=";")
                    for row in csv_reader:
                        src.append(row)
                self.sources.append(src)
                self.config.save_source_cache(source, self.digest_source(src))
            elif self.config.reload_data:
                self.digest_source(cache)

    def add_bank(self, bank):
        if bank.name not in self.banks:
            self.banks[bank.name] = bank
        else:
            for a in bank.accounts.values():
                self.banks[bank.name].add_account(a)

    def digest_source(self, src):
        if isinstance(src, Bank):
            bank = src
        else:
            bank = None
            if ActivoBank.is_source(src):
                print("Report source: ActivoBank.")
                bank = ActivoBank()
                bank.parse_source(src)
            elif PayPal.is_source(src):
                print("Report source: PayPal CSV.")
                bank = PayPal()
                bank.parse_source(src)
        if bank is None:
            print("Failed to identify the source of the report.")
            return None
        else:
            self.add_bank(bank)
            self.data.load_bank(bank)
            return bank

    def update(self):
        self.over.update()

    def run_clustering_kmeans(self, clusters=0, clear=False):
        cn, ci = self.data.classify_kmeans(clusters, init_clusters=self.autoclasses if not clear else {})
        self.clustering["kmeans"]["clusters"] = clusters
        self.clustering["kmeans"]["names"] = cn
        self.clustering["kmeans"]["idxs"] = ci
        self.extend_clases(cn, ci, clear=True)

    def extend_clases(self, class_names, class_idxs, clear=False):
        if clear:
            self.autoclasses = {}
        self.autoclasses.update({cn: ci for cn, ci in sorted(zip(class_names, class_idxs), key=lambda pair: pair[0])})

    def finalize_loading(self):
        self.data.finalize_loading()
        self.data.make_records_from_tagged("to_poup", "ActivoBank.Poupanças", new_tag="poup_in", invert_value=True)
        self.data.make_records_from_tagged("from_poup", "ActivoBank.Poupanças", new_tag="poup_out", invert_value=True)
        self.data.postprocess()
        self.save()
        self.update()

    def launchGUI(self, gui):
        self.finalize_before_gui()
        w = gui()
        return w.run(self)

    def finalize_before_gui(self):
        self.data.all_tags.append("<ANY>")
        self.data.all_tags = list(set(self.data.all_tags))
        self.data.all_tags.sort()
        d = self.data.m.date.min()
        today = datetime.now()
        if not pd.isnull(d):
            year = d.year
            month = d.month

            self.months = ["ALL"]
            while year != today.year or month != today.month:
                self.months.append((year, month))
                if month == 12:
                    month = 1
                    year += 1
                else:
                    month += 1

        self.months.append((today.year, today.month))
