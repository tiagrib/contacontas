# Copyright (c) 2022 Tiago Ribeiro
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT


from enum import Enum
from data.bank import Bank, Account, Segment, Movement
from .util import isFloat, isInt, extract_datetime_Ymd, extract_datetime_mov, extract_decimals
from decimal import *
import re

DEBUG = False

kRESUMO_DAS_CONTAS = "RESUMO DAS CONTAS"
kEOF = "DOCUMENTO DE INFORMAÇÃO SOBRE OS SERVIÇOS MÍNIMOS BANCÁRIOS"
kEOPFrom = "A TRANSPORTAR"
kEOPTo = "TRANSPORTE"
#kCONTA_SIMPLES = "CONTA SIMPLES N"
#kCONTA_TITULOS = "CONTA TITULOS N"
#kCONTA_POUPANCA = "ESCOLHA PRAZO J VENC"
kSALDO_INICIAL = "SALDO INICIAL"
kSALDO_FINAL = "SALDO FINAL"
kEXTRACTO_DATAS = "EXTRATO DE"
kCC_START = "OPERACAO DEBITO CREDITO"
kCC_END	 = "SALDO EM DIVIDA A DATA DO EXTRATO ATUAL"

def is_extracto_combinado(lines):
	return 'EXTRATO COMBINADO' in lines[4:15]

class ActivoBank(Bank):

	def __init__(self):
		super().__init__("ActivoBank")

	@staticmethod
	def is_source(lines):
		# first parser was written on this date, so we know it works from here
		if any('ACTVPTPL' in s for s in lines[5:15])  and \
			is_extracto_combinado(lines):
				return True
		return False

	def parse_source(self, all_lines):
		print("Parsing ActivoBank report... ", len(all_lines), "lines.")
		if is_extracto_combinado(all_lines):
			self.activo_bank_parse_extracto_combinado(all_lines)
		else:
			print("Unknown document type from ActivoBank.")

	class DocType(Enum):
		ExtractoCombinado = 1

	class MonthCombinedData():
		def __init__(self, lines, index):
			self._lines = lines
			self._index = index
			self.segments = {"Ordem":[], "CC":[]}
			self.cleanup_transport()
			self.extract_segments()

		def _l(self, key, idx=0):
			return self._lines[self._index[key][idx]]

		def check_block_delimiters(self, delim1, delim2, block_description):
			if len(self._index[delim1]) != len(self._index[delim2])>0:
				raise ValueError("Mismatching '" + delim1 + "/" + delim2 + "' block in " + block_description + "!")

		def cleanup_transport(self):
			self.check_block_delimiters(kEOPFrom, kEOPTo, "segment")

			for i in range(len(self._index[kEOPFrom])):
				i_from = self._index[kEOPFrom][i]
				i_to = self._index[kEOPTo][i]
				remove_num_lines = i_to - i_from + 1
				new_index = {}
				for k,v in self._index.items():
					for j in range(len(v)):
						if v[j] > i_from:
							v[j] = v[j] - remove_num_lines
						new_index[k] = v
				slice1 = self._lines[:i_from]
				slice2 = self._lines[i_to+1:]
				self._lines = slice1 + slice2
				self._index[kEOPFrom] = []
				self._index[kEOPTo] = []

		def extract_segments(self):

			

			def extract_a_ordem(self):
				self.start_value = extract_decimals(self._l(kSALDO_INICIAL))
				self.end_value = extract_decimals(self._l(kSALDO_FINAL))
				if DEBUG:
					print("A ORDEM")
					print("Start Value", self.start_value)
					print("End Value", self.end_value)
				prev_sum = self.start_value
				check_sum = prev_sum
				movements = []
				for i in range(self._index[kSALDO_INICIAL][0]+1, self._index[kSALDO_FINAL][0]-1):
					splits = self._lines[i].split(' ')
					date = extract_datetime_mov(splits[0]).replace(year=self.start_date.year)
					desc_start_i = 2
					desc_end_i = len(splits) - 2
					if isInt(splits[desc_end_i]):
						desc_end_i -= 1
						new_sum = splits[-2] + splits[-1]
					else:
						new_sum = splits[-1]
					if isInt(splits[desc_end_i - 1]) and len(splits[desc_end_i - 1])<3:
						desc_end_i -= 1

					value = Decimal(new_sum) - prev_sum
					check_sum += value
					prev_sum = Decimal(new_sum)
					assert(check_sum == prev_sum)
					desc = ' '.join(splits[desc_start_i:desc_end_i])
					movements.append(Movement(date, desc, value))
					if DEBUG: print("\t", movements[-1])
				self.segments["Ordem"].append((movements))

			def extract_cc(self):
				if len(self._index[kCC_START])>0:
					self._index[kCC_END] = self._index[kCC_END][1:]

					if DEBUG: print("CC")
					movement_lines = []
					for i in range(len(self._index[kCC_START])):
						start_idx = self._index[kCC_START][i]
						end_idx = self._index[kCC_END][i]
						
						for j in range(start_idx+1, end_idx):
							if len(list(re.finditer("(\d\d*\.\d{2}\s){2}",self._lines[j])))>0:
								movement_lines.append(self._lines[j])
							else:
								movement_lines[-1] += " " + self._lines[j]
					movements = []
					for ml in movement_lines:
						splits = ml.strip().split(' ')
						date = extract_datetime_mov(splits[0]).replace(year=self.start_date.year)					
						if isInt(splits[-2]):
							value = splits[-2] + splits[-1]
							desc = splits[2:-2]
						else:
							value = splits[-1]
							desc = splits[2:-1]
						value = float(value)
						desc = ' '.join(desc)
						movements.append(Movement(date, desc, value))
						if DEBUG: print("\t", movements[-1])
					self.segments["CC"].append((movements))

			self.start_date = extract_datetime_Ymd(self._l(kEXTRACTO_DATAS), 2)
			self.end_date = extract_datetime_Ymd(self._l(kEXTRACTO_DATAS), 4)
			if DEBUG:
				print("Start Date", self.start_date)
				print("Start Date", self.end_date)
			
			extract_a_ordem(self)
			extract_cc(self)

	def update_state(self, line):
		if line.lower() == "CONTA SIMPLES".lower():
			pass
		
	def _create_index_extracto_combinado(self, all_lines):
		index = {}
		keylines = [kRESUMO_DAS_CONTAS, kEOF, kCC_START #, kCONTA_POUPANCA
		]

		keylinestarts = [kEOPFrom, kEOPTo,# kCONTA_SIMPLES, kCONTA_TITULOS,
		kSALDO_INICIAL, kSALDO_FINAL, kEXTRACTO_DATAS, kCC_END]

		for s in keylines:
			index[s] = []
		for s in keylinestarts:
			index[s] = []
		for i in range(len(all_lines)):
			line = all_lines[i].strip()
			if line in keylines or any(line.startswith(s) for s in keylinestarts):
				if line not in keylines:
					key_index = [l for l in keylinestarts if line.startswith(l)][0]
				else:
					key_index = line
				index[key_index].append(i)
		return index
		

	def activo_bank_parse_extracto_combinado(self, all_lines):

		def extract_month(month_lines, month_indexes):
			month_lines.append(all_lines[start_line:end_line])
			month_index = {}
			for idx_key, idx_lines in index.items():
				month_index[idx_key] = [l-start_line for l in idx_lines if l >= start_line and l < end_line]
			month_indexes.append(month_index)
			return month_lines, month_indexes

		print("DocType: Extracto Combinado.")
		index = self._create_index_extracto_combinado(all_lines)
		month_lines = []
		start_line = index[kRESUMO_DAS_CONTAS][0]
		month_indexes = []
		for i in range(1,len(index[kRESUMO_DAS_CONTAS])):
			end_line = index[kRESUMO_DAS_CONTAS][i]
			month_lines, month_indexes = extract_month(month_lines, month_indexes)
			start_line = end_line

		end_line = index[kEOF][0]
		month_lines, month_indexes = extract_month(month_lines, month_indexes)
		
		months = []
		for i in range(len(month_lines)):
			months.append(ActivoBank.MonthCombinedData(month_lines[i], month_indexes[i]))

		for month in months:
			for account, movements in month.segments.items():
				for mov in movements:
					self.append_account_segment(account, mov)
