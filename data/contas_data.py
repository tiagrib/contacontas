from decimal import Decimal
import numpy as np
import pandas as pd
import numpy.lib.recfunctions as nrec
from . import cls, manipulation as manip




class ContasData:
    def __init__(self):
        self.num_b = 0
        self.num_a = 0
        self.num_m = 0
        # movements
        # load into a numpy array because it seems to be faster, later convert to pandas
        self._np_m = np.array([], dtype=np.dtype([
                ('fk_mov', np.int32), 
                ('bank', 'U32'), 
                ('account', 'U32'), 
                ('accb_key', 'U64'), 
                ('date', 'datetime64[s]'), 
                ('value', np.float32), 
                ('desc', 'U128'),
                ('fk_acc', np.int32),
                (manip.TAGS_FIELD, 'U32'),
                ('cumsum', np.float32),
                ('mask', np.bool_),
        ]))

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
        self.all_tags = []

    def prepare(self, num_banks, num_accounts, num_movs):
        self.b = manip.resize_table(self.b, num_banks)
        self.a = manip.resize_table(self.a, num_accounts)
        self._np_m = manip.resize_table(self._np_m, num_movs)


    def pre_record(self, bank, account, date, value, desc):
        b_key = self.b.loc[self.b['name']==bank]
        if b_key.empty:
            b_key = self.num_b
            self.num_b += 1
            self.b.iloc[b_key] = (b_key, bank)
        else:
            b_key = b_key.fk_bank.array[0]
        
        a_key = self.a.loc[(self.a.name==account) & (self.a.fk_bank==b_key)]
        if a_key.empty:
            a_key = self.num_a
            self.num_a += 1
            self.a.iloc[a_key] = (a_key, account, b_key)            
        else:
            a_key = a_key.fk_acc.array[0]

        m_key = self.num_m
        fields = (m_key, bank, account, bank + "." + account, np.datetime64(date), float(value), desc.lower(), a_key, "",0.0, True)
        self.num_m += 1
        self._np_m[m_key] = fields

    def classify_record(self, rec):
        if rec.bank != "PayPal" and "paypal" in rec.desc:
                rec[manip.TAGS_FIELD] = manip.append_tag(rec, "PayPal")
        return rec
    
    def append_record(self, bank, account, date, value, desc):
        m_key = self.num_m
        b_key = None
        a_key = None
        try:
            b_key = self.b.loc[self.b['name']==bank]
            b_key = b_key.fk_bank.array[0]
        except: None
        try:
            a_key = self.a.loc[(self.a.name==account) & (self.a.fk_bank==b_key)]
            a_key = a_key.fk_acc.array[0]
        except: None
        if b_key is None or a_key is None:
            print(f"Unable to add record to inexising bank account: {bank}.{account}!")
            return 
        self.m.loc[len(self.m)] = [m_key, bank, account, bank + "." + account, np.datetime64(date), float(value), desc.lower(), a_key, "",0.0, True]
        self.num_m += 1

    def finalize(self):
        
        # resize to fit actual data that made it through the precheck
        self._np_m = manip.resize_table(self._np_m, self.num_m)
        # convert to pd
        self.m = pd.DataFrame(self._np_m)
        self.mcoli = dict([(c, self.m.columns.get_loc(c)) for c in self.m.columns if c in self.m])

        # sort by date
        self.m['date'] = pd.to_datetime(self.m['date'])
        self.postprocess()

        mask = np.full(self.m.size,True)

        # compute cumulative sums per account
        account_cumsum = {}
        for r in pd.merge(self.b, self.a, on='fk_bank', suffixes=("_b", "_a")).itertuples(): 
            account_cumsum[r.name_b + '.' + r.name_a] = 0.0
        for i in range(self.num_m):
            entry = self.m.iloc[i]
            account_cumsum[entry.accb_key] += entry.value
            self.m.iat[i, self.mcoli['cumsum']] = account_cumsum[entry.accb_key]            

        # collect all existing tags
        all_unique_tags = self.m[manip.TAGS_FIELD].unique()
        for tagstring in all_unique_tags:
            tagsplit = tagstring.split(manip.TAG_SPLITTER)
            for t in tagsplit:
                t = t.lower().strip()
                if not t in self.all_tags:
                    self.all_tags.append(t)
        print("All existing tags: ", self.all_tags)
        manip.cluster(self.m,"desc")
        return self.m
    
    def postprocess(self):
        self.preclassify()
        self.aggregated_reductions()
        self.m.sort_values(by='date', inplace = True)
        self.m.sort_values(by='account', inplace = True, kind='stable')
        self.m.reset_index(drop=True)

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
                                ])): "paypal_cash_in,internal",

                cls.t_and(
                    cls.t_eq("bank", "PayPal"),
                    cls.t_contains_words("desc", "general withdrawal - bank account")): 
                                    "paypal_cash_out,internal",

                cls.t_and(
                    cls.t_and(
                        cls.t_eq("bank", "ActivoBank"),
                        cls.t_eq("account", "Ordem")),
                    cls.t_contains_words("desc", "pagamento cartao de credito")
                                    ): "cc_cash_out,internal",
                
                cls.t_and(
                    cls.t_and(
                        cls.t_eq("bank", "ActivoBank"),
                        cls.t_eq("account", "CC")),
                    cls.t_contains_words("desc", "pagamento cartao de credito")
                                    ): "cc_cash_in,internal",

                cls.t_and(
                    cls.t_not(cls.t_eq("bank", "PayPal")),
                    cls.t_and(
                        cls.t_contains_words("desc", "paypal"),
                        cls.t_lessthan("value", 0)
                    )
                ): "to_paypal,internal",

                cls.t_and(
                    cls.t_not(cls.t_eq("bank", "PayPal")),
                    cls.t_and(
                        cls.t_contains_words("desc", "paypal"),
                        cls.t_greaterthan("value", 0)
                    )
                ): "from_paypal,internal",
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
