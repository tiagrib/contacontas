class Overviews:
    def __init__(self, cc):
        self.cc = cc


    def update(self):
        self.months = list(set([(d.year, d.month) for d in self.cc.data.m.date.unique()]))
        self.months.sort()
        self.accounts_monthly = {}
        self.acc_sum = {}
        for ym in self.months:
            md = self.cc.data.get_monthly(ym[0], ym[1])
            print("\n", ym, 'ALL', "POS:", md[md.value>=0].value.sum(), "NEG:", md[md.value<0].value.sum(), )

            for bank, binfo in self.cc.banks.items():
                bdata = md[md.bank==bank]
                for account in binfo.accounts:
                    adata = md[md.account==account]
                    adata = adata[adata.internal==False]
                    if account not in self.acc_sum:
                        self.acc_sum[account] = 0 
                    self.acc_sum[account] += adata.value.sum()                    
                    print(ym, bank, account, "POS:", adata[adata.value>=0].value.sum(), "NEG:", adata[adata.value<0].value.sum(), "SUM:", self.acc_sum[account])
        