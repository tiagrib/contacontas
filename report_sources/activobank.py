# Copyright (c) 2022 Tiago Ribeiro
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT


from enum import Enum
from data.bank import Bank, Account, Segment, Movement
from .util import isFloat, isInt, extract_datetime_Ymd, extract_datetime_mov, extract_decimals
from decimal import *
import re
import dateutil

DEBUG = False

kEC_RESUMO_DAS_CONTAS = "RESUMO DAS CONTAS"
kEC_EOF = "DE INFORMAÇÃO SOBRE OS SERVIÇOS MÍNIMOS BANCÁRIOS"
kEC_EOPFrom = "A TRANSPORTAR"
kEC_EOPTo = "TRANSPORTE"
kEC_SALDO_INICIAL = "SALDO INICIAL"
kEC_SALDO_FINAL = "SALDO FINAL"
kEC_EXTRACTO_DATAS = "EXTRATO DE"
kEC_CC_START = "OPERACAO DEBITO CREDITO"
kEC_CC_END	 = "SALDO EM DIVIDA A DATA DO EXTRATO ATUAL"

kCC_MOV_START = "DETALHE DOS MOVIMENTOS"
kCC_MOV_END = "CE05822/01"
kCC_DATE = "Emissão do Extrato Atual:"

def is_extracto_combinado(lines):
	return 'CE05669/01' in lines[0:3]

def is_extracto_cc(lines):
	return 'CE05822/01' in lines[0:3]

class ActivoBank(Bank):

	def __init__(self):
		super().__init__("ActivoBank")

	@staticmethod
	def is_source(lines):
		# first parser was written on this date, so we know it works from here
		if (	'CE05669/01' in  lines[0:3] or
	  			'CE05822/01' in lines[0:3]):
			if is_extracto_combinado(lines):
				return True
			elif is_extracto_cc(lines):
				return True
			else:
				return False
		return False

	def parse_source(self, all_lines):
		print("Parsing ActivoBank report... ", len(all_lines), "lines.")
		if is_extracto_combinado(all_lines):
			return self.activo_bank_parse_extracto_combinado(all_lines)
		elif is_extracto_cc(all_lines):
			return self.activo_bank_parse_extracto_cc(all_lines)
		else:
			print("Unknown document type from ActivoBank.")
			return None

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
			self.check_block_delimiters(kEC_EOPFrom, kEC_EOPTo, "segment")

			for i in range(len(self._index[kEC_EOPFrom])):
				i_from = self._index[kEC_EOPFrom][i]
				i_to = self._index[kEC_EOPTo][i]
				remove_num_lines = i_to - i_from + 1
				new_index = {}
				for k,v in self._index.items():
					new_index[k] = v
					for j in range(len(v)):
						if v[j] > i_from:
							v[j] = v[j] - remove_num_lines
						new_index[k] = v
				self._index = new_index
				slice1 = self._lines[:i_from]
				slice2 = self._lines[i_to+1:]
				self._lines = slice1 + slice2
			self._index[kEC_EOPFrom] = []
			self._index[kEC_EOPTo] = []

		def extract_segments(self):

			def extract_a_ordem(self):
				self.start_value = extract_decimals(self._l(kEC_SALDO_INICIAL), join=True)
				self.end_value = extract_decimals(self._l(kEC_SALDO_FINAL), join=True)
				if DEBUG:
					print("A ORDEM")
					print("Start Value", self.start_value)
					print("End Value", self.end_value)
				prev_sum = self.start_value
				check_sum = prev_sum
				movements = []
				for i in range(self._index[kEC_SALDO_INICIAL][0]+1, self._index[kEC_SALDO_FINAL][0]):
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
				if len(self._index[kEC_CC_START])>0:
					self._index[kEC_CC_END] = self._index[kEC_CC_END][1:]

					if DEBUG: print("CC")
					movement_lines = []
					for i in range(len(self._index[kEC_CC_START])):
						start_idx = self._index[kEC_CC_START][i]
						end_idx = self._index[kEC_CC_END][i]
						# ((\d?\d\.\d\d\s\d?\d.\d\d)([\w\s\-\>\<]|(\D\.\D))+(\d*\d.\d\d(?=\s)))
						expr = r"((?:\d?\d\.\d\d\s\d?\d.\d\d)(?:.(?![01]?\d\.\d\d\s[01]?\d\.\d\d\s\D))+)+"
						txt = ' '.join(self._lines[start_idx+1: end_idx])
						movement_lines.extend([m for m in re.findall(expr, txt)])
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
						desc = ' '.join(desc).lower().strip()
						if (not "pagamento cartao de credito" in desc and
		  						not desc.startswith('cred.')):
							value = -value
						movements.append(Movement(date, desc, value))
						if DEBUG: print("\t", movements[-1])
					self.segments["CC"].append((movements))

			self.start_date = extract_datetime_Ymd(self._l(kEC_EXTRACTO_DATAS), 2)
			self.end_date = extract_datetime_Ymd(self._l(kEC_EXTRACTO_DATAS), 4)
			if DEBUG:
				print("Start Date", self.start_date)
				print("Start Date", self.end_date)
			
			extract_a_ordem(self)
			extract_cc(self)

	def update_state(self, line):
		if line.lower() == "CONTA SIMPLES".lower():
			pass
		
	def _create_index_extracto(self, all_lines, keylines, keylinestarts, keylinecontains):
		index = {}

		for keygroup in [keylines, keylinestarts, keylinecontains]:
			for k in keygroup:
				index[k] = []
		
		for i in range(len(all_lines)):
			line = all_lines[i].strip()
			line_in_keylines = line in keylines
			line_in_keylinestarts = any(line.startswith(s) for s in keylinestarts)
			line_in_keylinecontains = any(s in line for s in keylinecontains)
			if line_in_keylines or line_in_keylinestarts or line_in_keylinecontains:
				if line_in_keylinestarts:
					key_index = [l for l in keylinestarts if line.startswith(l)][0]
				elif line_in_keylinecontains:
					key_index = [s for s in keylinecontains if s in line][0]
				else:
					key_index = line
				index[key_index].append(i)
		return index
	
	def _create_index_extracto_combinado(self, all_lines):
		keylines = [kEC_RESUMO_DAS_CONTAS, kEC_CC_START ]
		keylinestarts = [kEC_EOPFrom, kEC_EOPTo,kEC_SALDO_INICIAL, kEC_SALDO_FINAL, kEC_EXTRACTO_DATAS, kEC_CC_END]
		keylinecontains = [kEC_EOF]
		return self._create_index_extracto(all_lines, keylines, keylinestarts, keylinecontains)
		

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
		start_line = index[kEC_RESUMO_DAS_CONTAS][0]
		month_indexes = []
		for i in range(1,len(index[kEC_RESUMO_DAS_CONTAS])):
			end_line = index[kEC_RESUMO_DAS_CONTAS][i]
			month_lines, month_indexes = extract_month(month_lines, month_indexes)
			start_line = end_line

		end_line = index[kEC_EOF][0]
		month_lines, month_indexes = extract_month(month_lines, month_indexes)
		
		months = []
		for i in range(len(month_lines)):
			months.append(ActivoBank.MonthCombinedData(month_lines[i], month_indexes[i]))

		for month in months:
			for account, movements in month.segments.items():
				for mov in movements:
					self.append_account_segment(account, mov)
		return months

	def _create_index_extracto_cc(self, all_lines):
		keylines = [kCC_MOV_START, kCC_MOV_END ]
		keylinestarts = [kCC_DATE]
		keylinecontains = []
		return self._create_index_extracto(all_lines, keylines, keylinestarts, keylinecontains)

	def activo_bank_parse_extracto_cc(self, all_lines):

		def extract_month(month_lines, i):
			# movs starts 5 lines after key
			mov_start_i = index[kCC_MOV_START][i] + 5
			mov_end_i = index[kCC_MOV_END][i]
			month_lines.append(all_lines[mov_start_i:mov_end_i])
			return month_lines
		
		print("DocType: Extracto Cartão de Crédito.")
		index = self._create_index_extracto_cc(all_lines)
		index[kCC_MOV_END] = index[kCC_MOV_END][1:]
		next_mov_end_i = 0
		clean_mov_start = []
		mov_started = False
		for s in index[kCC_MOV_START]:
			if next_mov_end_i >= len(index[kCC_MOV_END]):
				index[kCC_MOV_END].append(len(all_lines))
				break
			if s > index[kCC_MOV_END][next_mov_end_i]:
				next_mov_end_i += 1
				mov_started = False
			if mov_started:
				if s < index[kCC_MOV_END][next_mov_end_i]:
					continue
			mov_started = True
			clean_mov_start.append(s)
		index[kCC_MOV_START] = clean_mov_start
		num_months = len(index[kCC_MOV_START])

		assert(num_months == len(index[kCC_MOV_END]))
		assert(num_months == len(index[kCC_DATE]))

		month_lines = []
		
		for i in range(0,num_months):
			month_lines = extract_month(month_lines, i)

		for lines in month_lines:
			movements = []
			for l in lines:
				try:
					split = l.split()
					date = dateutil.parser.parse(split[0])
					if split[-2].isdigit() and len(split[-2]) == 1: # assume movements are not > 9999
						value = split[-2] + split[-1]
						desc = split[2:-2]
					else:
						value = -float(split[-1])
						desc = " ".join(split[2:-1]).lower().strip()
						if (	'pagamento cartao de credito' in desc or
		  						desc.startswith('cred.')):
							value *= -1
						movements.append(Movement(date, desc, value))
				except: pass
			self.append_account_segment("CC", movements)
