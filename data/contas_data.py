from decimal import Decimal
import numpy as np
import pandas as pd
import numpy.lib.recfunctions as nrec


def _resize_table(t, n):
    rows_diff = n - t.shape[0]
    if isinstance(t, pd.DataFrame):
        if rows_diff > 0:
            return _pd_extend_table(t, n)
        elif rows_diff < 0:
            return _pd_downsize_table(t, n)
        else: return t
    elif isinstance(t, np.ndarray):
        if rows_diff > 0:
            return _np_extend_table(t, n)
        elif rows_diff < 0:
            return _np_resize_table(t, n)
        else: return t
        

def _pd_extend_table(t, n):
    new_empty_n = max(0, int(n*1.1) - t.shape[0])
    if new_empty_n:
        return pd.concat([t, pd.DataFrame(0, index=np.arange(new_empty_n), columns=t.columns)])
    else:
        return t
    
def _pd_downsize_table(t, n):
    n_diff = t.shape[0] - n
    if n_diff > 0:
        t.drop(t.tail(n_diff).index, inplace=True)
    return t
    
def _np_extend_table(t, n):
    new_empty_n = max(0, int(n*1.1) - t.shape[0])
    if new_empty_n:
        return np.resize(t, new_empty_n)
    else:
        return t

def _np_resize_table(t, n):
    return np.resize(t, n)

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
                ('date', 'datetime64[s]'), 
                ('value', np.float32), 
                ('desc', 'U128'),
                ('fk_acc', np.int32),
                ('classification', 'U32'),
                ('sum', np.float32),
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

    def prepare(self, num_banks, num_accounts, num_movs):
        self.b = _resize_table(self.b, num_banks)
        self.a = _resize_table(self.a, num_accounts)
        self._np_m = _resize_table(self._np_m, num_movs)


    def record(self, bank, account, date, value, desc):
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
        fields = (m_key, bank, account, np.datetime64(date), float(value), desc.lower(), a_key, "",0.0, True)
        if self.precheck_record(fields):
            self.num_m += 1
            self._np_m[m_key] = fields

    def precheck_record(self, rec):
        if rec[1] == "PayPal":
            if  "bank deposit to pp" in rec[5] or "general credit card deposit" in rec[5]:
                return False
        return True

    def classify_record(self, rec):
        if rec.bank != "PayPal" and "paypal" in rec.desc:
                rec.classification = "PayPal"
        return rec

    def finalize(self):
        
        # resize to fit actual data that made it through the precheck
        self._np_m = _resize_table(self._np_m, self.num_m)
        # convert to pd
        self.m = pd.DataFrame(self._np_m)

        # sort by date
        self.m['date'] = pd.to_datetime(self.m['date'])
        self.m.sort_values(by='date')

        # classify records
        self.m = self.m.apply(lambda rec : self.classify_record(rec), axis=1)

        mask = np.full(self.m.size,True)
        # remove paypal 
#        pp_refunded = np.flatnonzero(np.core.defchararray.find(view['desc'],"refund")!=-1)
#        pp_refunded = self.m[pp_refunded]['bank']=="PayPal"
#        mask[pp_refunded] = False
#        for d in self.m[pp_refunded]['desc']:
#            key = d.split(' ')[-1]
            #for each ellement in following array
            #set mask to false
#            np.flatnonzero(np.core.defchararray.find(view['desc'],"5637722933")!=-1)

        # compute cumulative sums per account
        account_sum = {}
        for r in pd.merge(self.b, self.a, on='fk_bank', suffixes=("_b", "_a")).itertuples(): 
            account_sum[r.name_b + '.' + r.name_a] = 0.0
        
        for i in range(self.num_m):
            entry = self.m.iloc[i]
            acc_key = entry.bank + "." + entry.account
            account_sum[acc_key] += entry.value
            self.m.at[i, 'sum'] = account_sum[acc_key]
            

        return self.m