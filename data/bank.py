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

    def append_segment(self, movements):
        self.segments.append(Segment(self, movements))

class Bank:
    def __init__(self, name):
        self.name = name
        self.accounts = {}

    @staticmethod
    def is_source(src):
        raise NotImplementedError()

    def parse_source(self, src):
        raise NotImplementedError()

    def append_account_segment(self, account, movements):
        if account not in self.accounts:
            self.accounts[account] = Account(account, self)
        self.accounts[account].append_segment(movements)
        