class Overviews:

    class AccountMonthly:
        def __init__(self, ym, info, data, prev_month = None, initial_value = None):
            assert(initial_value is None or prev_month is None)
            self.ym = ym
            self.prev_month = prev_month
            self.next_month = None
            if self.prev_month:
                self.prev_month.next_month = self
            self.initial_value = 0 if initial_value is None else initial_value
            if self.prev_month:
                self.initial_value = self.prev_month.sum
            self.info = info
            self.data = data
            self.sum = self.initial_value + data.value.sum()
            self.gain = data[data.value>=0].value.sum()
            self.loss = data[data.value<0].value.sum()
            acc_name = "ALL"
            if info:
                acc_name = f"{info.bank.name}.{info.name}"
            print(ym, acc_name, "START:", self.initial_value, "GAIN:", self.gain, "LOSS:", self.loss, "SUM:", self.sum)

    def __init__(self, cc):
        self.cc = cc
        self.accounts_by_month = {}
        self.accounts_monthly = {}

    def update(self):
        self.months = list(set([(d.year, d.month) for d in self.cc.data.m.date.unique()]))
        self.months.sort()
        prev_month = {}

        def add_monthly(ym, account, data, initial_value = None):
            data = data[data.internal==False]
            prev_acc_month = prev_month[account] if account in prev_month else None
            initial_value = account.initial_value if prev_acc_month is None and account is not None else initial_value

            if not ym in self.accounts_by_month:
                self.accounts_by_month[ym] = {}
            if account not in self.accounts_monthly:
                self.accounts_monthly[account] = {}

            self.accounts_by_month[ym][account] = Overviews.AccountMonthly(ym, account, data, prev_month=prev_acc_month, initial_value=initial_value)
            self.accounts_monthly[account][ym] = self.accounts_by_month[ym][account]

            prev_month[account] = self.accounts_by_month[ym][account]


        for ym in self.months:
            md = self.cc.data.get_monthly(ym[0], ym[1])
            #print("\n", ym, 'ALL', "POS:", md[md.value>=0].value.sum(), "NEG:", md[md.value<0].value.sum(), )
            add_monthly(ym, None, md)

            for bank in self.cc.banks.values():
                for account in bank.accounts.values():
                    amdata = md[md.account==account.name]
                    add_monthly(ym, account, amdata)
