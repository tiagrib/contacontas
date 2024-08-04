class Overviews:

    class AccountMonthly:
        def __init__(self, ym, info, data, prev_month = None, initial_value = None):
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
            print(f"{ym} {acc_name:>20} START: {self.initial_value:.2f} GAIN: {self.gain:.2f} LOSS: {self.loss:.2f} BALANCE: {self.sum:.2f}")

    def __init__(self, cc):
        self.cc = cc
        self.accounts_by_month = {}
        self.accounts_monthly = {}

    def update(self):
        prev_month = {}

        def add_monthly(ym, account, data, initial_value = None):
            #if not account or not account.all_internal:
                #data = data[data.internal==False]
            prev_acc_month = prev_month[account] if account in prev_month else None
            if prev_acc_month is not None:
                initial_value = prev_acc_month.sum
            else:
                if account is not None:
                    initial_value = account.initial_value

            if not ym in self.accounts_by_month:
                self.accounts_by_month[ym] = {}
            if account not in self.accounts_monthly:
                self.accounts_monthly[account] = {}

            self.accounts_by_month[ym][account] = Overviews.AccountMonthly(ym, account, data, prev_month=prev_acc_month, initial_value=initial_value)
            self.accounts_monthly[account][ym] = self.accounts_by_month[ym][account]

            prev_month[account] = self.accounts_by_month[ym][account]
            return self.accounts_by_month[ym][account]

        all_initial_value = 0
        for bank in self.cc.banks.values():
            for account in bank.accounts.values():
                all_initial_value += account.initial_value
        first_month = True
        prev_all_balance = None

        for ym in self.cc.data.months:
            md = self.cc.data.get_monthly(ym[0], ym[1])
            #print("\n", ym, 'ALL', "POS:", md[md.value>=0].value.sum(), "NEG:", md[md.value<0].value.sum(), )
            print()
            if first_month:
                prev_all_balance = add_monthly(ym, None, md, initial_value=all_initial_value)
            else:
                prev_all_balance = add_monthly(ym, None, md, prev_all_balance.sum)

            for bank in self.cc.banks.values():
                for account in bank.accounts.values():
                    amdata = md[md.account==account.name]
                    add_monthly(ym, account, amdata)
