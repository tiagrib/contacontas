from decimal import Decimal
import hashlib
from pathlib import Path
import pickle
import numpy as np
import pandas as pd
import numpy.lib.recfunctions as nrec

from data.bank import Bank
from . import cls, manipulation as manip


def create_record_hash(bank, account, date, value, desc):
	sha = hashlib.md5(str((bank, account, date, value, desc)).encode("utf-8"))
	return sha.hexdigest()

class ContasData:
	def __init__(self):

		pd.set_option('display.max_rows', None)
		pd.set_option('display.max_columns', None)
		pd.set_option('display.width', None)
		pd.set_option('display.max_colwidth', None)

		self.num_b = 0
		self.num_a = 0
		self.num_m = 0
		# movements
		

		# account
		self.a = np.array([], dtype=np.dtype([
			('fk_acc', np.int32), 
			('name', 'U32'), 
			('fk_bank', np.int32)
		]))

		# bank
		self.b = np.array([], dtype=np.dtype([
			('fk_bank', np.int32), 
			('name', 'U32')
		]))

		self.a = pd.DataFrame(np.resize(self.a, 1).T)
		self.b = pd.DataFrame(np.resize(self.b, 1).T)
		self._np_m = self.make_loading_block()
		self.columns = self._np_m.dtype.names
		self.col_i = dict([(c, i) for i, c in enumerate(self.columns)])
		self.m = pd.DataFrame(dict([(d[0], pd.Series(dtype=pd.StringDtype() if d[1][1]=='U' else d[1])) for d in self._np_m.dtype.descr]))
		#self.m.set_index('sha')
		self.all_tags = []
		self.mcoli = {}
		self.months = []

	def make_loading_block(self):
		return np.array([], dtype=np.dtype([
				('bank', 'U32'), 
				('account', 'U32'), 
				('date', 'datetime64[s]'), 
				('year', np.int16),
				('month', np.int8),
				('value', np.float32), 
				('desc', 'U128'),
				(manip.TAGS_FIELD, 'U32'),
				('mask', np.bool_),
				(manip.INTERNAL_FIELD, np.bool_),
				('sha', 'U64'),
		]))

	def init_loading_bank_account(self, bank:Bank, account:str):
		self.allocate(1, 1, len(bank.get_account_records(account)))

	def allocate(self, num_banks, num_accounts, num_movs):
		self.b = manip.resize_table(self.b, self.num_b + num_banks)
		self.a = manip.resize_table(self.a, self.num_a + num_accounts)
		# load into a numpy array because it seems to be faster, later convert to pandas
		self._np_m = self.make_loading_block()
		self._np_m = manip.resize_table(self._np_m, self.num_m + num_movs)
		self._loading_m = 0

	def load_bank(self, bank):
		for a in bank.accounts:
			self.init_loading_bank_account(bank, a)
			records = bank.get_account_records(a)
			for r in records:
				self._add_record_preallocated(*r)
			self.finalize_loading_bank_account()

	def add_record(self, bank, account, date, value, desc):
		self.allocate(1,1,1)
		self._add_record_preallocated(bank, account, date, value, desc)
		self.merge_loading_cache_to_m()

	def _add_record_preallocated(self, bank, account, date, value, desc, tag='', internal=False):
		sha = create_record_hash(bank, account, np.datetime64(date), float(value), desc.lower())
		if sha in self.m['sha'].values:
			print("Skip duplicate record: ", bank, account, np.datetime64(date), float(value), desc.lower())
			return
		duplicate = 1
		desc_base = desc
		while sha in self._np_m['sha']:
			desc = f"{desc_base}({duplicate})"
			sha = create_record_hash(bank, account, np.datetime64(date), float(value), desc.lower())
			duplicate += 1
					
		fields = (bank, account, np.datetime64(date), date.year, date.month, float(value), desc.lower(), tag, True, internal, sha)
		self.num_m += 1
		self._np_m[self._loading_m] = fields    
		self._loading_m += 1
	
	def set_tag_over_indices(self, indices, tag):
		col = self.m.columns.get_loc(manip.TAGS_FIELD)
		for i in indices:
			self.m.iloc[i, col] = manip.append_tag(self.m.iloc[i], tag)

	def get_monthly(self, year, month):
		return self.m[(self.m.year == year) & (self.m.month == month)]

	def convert_loading_cache_to_m(self):
		# resize to fit actual data that made it
		self._np_m = manip.resize_table(self._np_m, self._loading_m)
		# convert to pd
		m = pd.DataFrame(self._np_m)
		#m = m.set_index('sha')
		return m

	def finalize_loading_bank_account(self):
		m = self.convert_loading_cache_to_m()
		self.m = pd.concat([self.m, m])

	def finalize_loading(self):
		self.preclassify()
	
	def get_tagged_records(self, tag):
		return self.m[manip.col_contains_tag(self.m[manip.TAGS_FIELD], tag)]
	
	def postprocess(self):
		
		self.m.sort_values(by='account', inplace = True, kind='stable')
		self.m.sort_values(by='date', inplace = True)

		self.months = list(set([(d.year, d.month) for d in self.m.date.unique()]))
		self.months.sort()

		# collect all existing tags
		all_unique_tags = self.m[manip.TAGS_FIELD].unique()
		for tagstring in all_unique_tags:
			if tagstring is None:
				tagstring = ""
			tagsplit = tagstring.split(manip.TAG_SPLITTER)
			for t in tagsplit:
				t = t.lower().strip()
				if not t in self.all_tags:
					self.all_tags.append(t)
	

	def preclassify(self):
		# classify records based on account and movement types
		# before proceeding with aggregation reductions
		stack = cls.classifier_stack()
		stack.add_classifier(cls.test_classifier(classes = {
				cls.t_and(
					cls.t_eq("bank", "PayPal"),
					cls.t_contains_words("desc", 
							 [  "bank deposit to pp", 
								"general credit card deposit", 
								"top up",
								"general withdrawl - bank account"
								])): "paypal_cash_in",

				cls.t_and(
					cls.t_eq("bank", "PayPal"),
					cls.t_contains_words("desc", 
						  [ "general withdrawal - bank account",
							"general credit card withdrawal" 
							])): "paypal_cash_out",

				cls.t_and(
					cls.t_and(
						cls.t_eq("bank", "ActivoBank"),
						cls.t_eq("account", "Ordem")),
					cls.t_contains_words("desc", "pagamento cartao de credito")
									): "cc_cash_out",
				
				cls.t_and(
					cls.t_and(
						cls.t_eq("bank", "ActivoBank"),
						cls.t_eq("account", "CC")),
					cls.t_contains_words("desc", "pagamento cartao de credito")
									): "cc_cash_in",

				cls.t_and(
					cls.t_not(cls.t_eq("bank", "PayPal")),
					cls.t_and(
						cls.t_contains_words("desc", "paypal"),
						cls.t_lessthan("value", 0)
					)
				): "to_paypal",

				cls.t_and(
					cls.t_not(cls.t_eq("bank", "PayPal")),
					cls.t_and(
						cls.t_contains_words("desc", "paypal"),
						cls.t_greaterthan("value", 0)
					)
				): "from_paypal",

				cls.t_and(
					cls.t_and(
						cls.t_eq("bank", "ActivoBank"),
						cls.t_eq("account", "Ordem")),
					cls.t_contains_words("desc", "liq parcial dep prazo")
				): "from_poup",

				cls.t_and(
					cls.t_and(
						cls.t_eq("bank", "ActivoBank"),
						cls.t_eq("account", "Ordem")),
					cls.t_contains_words("desc", "reforco dep prazo")
				): "to_poup",
		}))

		self.m = stack.run(self.m)

	def aggregated_reductions(self):
		# Reduce bank-paypal movements in PayPal account        
		manip.aggregate_by_month_from_tag(self, "PayPal", "PayPal", "paypal_cash_in", 'sum')
		manip.aggregate_by_month_from_tag(self, "PayPal", "PayPal", "paypal_cash_out", 'sum')
		manip.aggregate_by_month_from_tag(self, "ActivoBank", "Ordem", "to_paypal", 'sum')
		manip.aggregate_by_month_from_tag(self, "ActivoBank", "Ordem", "from_paypal", 'sum')
		manip.aggregate_by_month_from_tag(self, "ActivoBank", "CC", "to_paypal", 'sum')
		manip.aggregate_by_month_from_tag(self, "ActivoBank", "CC", "from_paypal", 'sum')
		manip.aggregate_by_month_from_tag(self, "ActivoBank", "CC", "cc_cash_in", 'sum')
		manip.aggregate_by_month_from_tag(self, "ActivoBank", "Ordem", "cc_cash_out", 'sum')

	def classify_kmeans(self, n_clusters=0, init_clusters={}):
		return manip.cluster(self.m, "desc", n_clusters, init_clusters)
