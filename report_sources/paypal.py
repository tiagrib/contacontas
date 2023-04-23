from datetime import datetime
from data.bank import Bank, Account, Segment, Movement
from .util import extract_datetime_mdY, extract_decimals

class PayPal(Bank):

	def __init__(self):
		super().__init__("PayPal")

	@staticmethod
	def is_source(src):
		# first parser was written on this date, so we know it works from here
		return isinstance(src, list) and len(src)>0 and len(src[0])==18
		
	def parse_source(self, src):
		movs = []
		for line in src[1:]:
			s_date = extract_datetime_mdY(line[0])
			s_desc = line[3]
			s_value = extract_decimals(line[7])
			s_id = line[9]
			s_entity = line[11]
			s_invoice = line[16]
			s_reference = line[17]
			movs.append(Movement(s_date, ' '.join([s_entity, s_desc, s_invoice]), s_value))
		self.append_account_segment("PayPal", movs)