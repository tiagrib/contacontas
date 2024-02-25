class Movement():
		def __init__(self, date, desc, value):
			self.date = date
			self.desc = desc
			self.value = value

		def __str__(self):
			return f"{self.date} | {self.value:10.2f} | {self.desc}"

class Segment():
	def __init__(self, account, movements):
		self.account = account
		self.movements = movements

class Account():
	def __init__(self, account_name, bank):
		self.bank = bank
		self.name = account_name
		self.segments = []
		self.initial_value = 0

	def append_segment(self, movements):
		self.segments.append(Segment(self, movements))

class Bank:
	def __init__(self, name):
		self.name = name
		self.accounts = {}

	@staticmethod
	def is_source(src):
		raise NotImplementedError()

	def add_account(self, acc):
		if isinstance(acc, Account):
			if acc.name not in self.accounts:
				self.accounts[acc.name] = acc
			else:
				for s in acc.segments:
					self.append_account_segment(acc.name, s)
		else:
			self.append_account_segment(acc, [])

	def parse_source(self, src):
		raise NotImplementedError()

	def append_account_segment(self, account, movements):
		if account not in self.accounts:
			self.accounts[account] = Account(account, self)
		self.accounts[account].append_segment(movements)

	def get_records(self):
		records = []
		for account in self.accounts.values():
			for segment in account.segments:
				for mov in segment.movements:
					records.append([self.name, account.name, mov.date, mov.value, mov.desc])
		return records
	
	def get_account_records(self, account):
		if account in self.accounts:
			records = []
			for segment in self.accounts[account].segments:
				for mov in segment.movements:
					records.append([self.name, account, mov.date, mov.value, mov.desc])
			return records
		else:
			 return None