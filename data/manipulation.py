from data.bank import Movement
import calendar
import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

TAG_SPLITTER = ','
TAGS_FIELD = 'tags'

def resize_table(t, n):
    rows_diff = n - t.shape[0]
    if isinstance(t, pd.DataFrame):
        if rows_diff > 0:
            return pd_extend_table(t, n)
        elif rows_diff < 0:
            return pd_downsize_table(t, n)
        else: return t
    elif isinstance(t, np.ndarray):
        if rows_diff > 0:
            return np_extend_table(t, n)
        elif rows_diff < 0:
            return np_resize_table(t, n)
        else: return t
        

def pd_extend_table(t, n):
    new_empty_n = max(0, int(n*1.1) - t.shape[0])
    if new_empty_n:
        return pd.concat([t, pd.DataFrame(0, index=np.arange(new_empty_n), columns=t.columns)])
    else:
        return t
    
def pd_downsize_table(t, n):
    n_diff = t.shape[0] - n
    if n_diff > 0:
        t.drop(t.tail(n_diff).index, inplace=True)
    return t
    
def np_extend_table(t, n):
    new_empty_n = max(0, int(n*1.1) - t.shape[0])
    if new_empty_n:
        return np.resize(t, new_empty_n)
    else:
        return t

def np_resize_table(t, n):
    return np.resize(t, n)

def aggregate_by_month_from_tag(cd, bank, account, tag, operation):
    data = cd.m[(cd.m.bank==bank) & (cd.m.account==account) & col_contains_tag(cd.m.tags, tag)]
    aggregated = aggregate_by_month(data, operation, tag)
    cd.m.loc[data.index,'mask']=False
    for i in range(len(aggregated)):
        entry = aggregated.iloc[i]
        cd.append_record(bank, account, entry['date'], entry['value'], entry['desc'])

def aggregate_by_month(data, operation, desc_prefix):
    res = np.array([], dtype=np.dtype([
            ('date', 'datetime64[s]'), 
            ('value', np.float32), 
            ('desc', 'U128')
    ]))
    
    agg_sums_by_month = data.resample(rule='M', on='date').agg({'value':operation})
    res = resize_table(res, agg_sums_by_month.size)
    for i in range(agg_sums_by_month.size): 
        item = agg_sums_by_month.iloc[i]
        i_date = item.name
        i_date.replace(day=calendar.monthrange(i_date.year, i_date.month)[1])
        desc = f"{desc_prefix} {operation}.{i_date.year}.{i_date.month}"
        res[i] = (i_date, float(item.value), desc)
    return pd.DataFrame(res)

def set_mask(data, tag, mask):
    data.loc[col_contains_tag(data[TAGS_FIELD], tag), 'mask'] = mask

def append_tag(rec, tag):
    if rec.tags==None or rec.tags=="":
        return tag
    return rec.tags + TAG_SPLITTER + tag

def col_contains_tag(col, tag):
    return col.apply(lambda x: 
                  ((TAG_SPLITTER not in x) and 
                    x == tag) or
                  any(tag==t for t in x.split(TAG_SPLITTER)))

def contains_tag(rec, tag):
    return ((TAG_SPLITTER not in rec.tags) and 
            rec.tags == tag) or \
        any(tag == t for t in rec.tags.split(TAG_SPLITTER))

def kmeans(data, **kwargs):
    tfidf = TfidfVectorizer()
    vec = tfidf.fit_transform(data.to_list())
    kmeans = KMeans(**kwargs)
    kmeans.fit(vec)
    clusters = kmeans.predict(vec)
    unique_clusters, cluster_description_indices = np.unique(clusters, return_index=True)
    cluster_indices = [np.where(clusters==i)[0] for i in unique_clusters]
    cluster_descriptions = []
    for idxs in cluster_indices:
        cluster_desc_vec = tfidf.transform(data.iloc[idxs].to_list()).toarray()
        # get common features across cluster entries
        common_features = tfidf.get_feature_names_out()[np.nonzero(np.prod(cluster_desc_vec,axis=0))[0]]
        # remove feature names starting or ending with numbers
        common_features = [f for f in common_features if not (f[0].isdigit() or f[-1].isdigit())]
        cluster_desc = ' '.join(common_features)
        cluster_descriptions.append(cluster_desc)
    return cluster_descriptions, cluster_indices

def cluster(df, field, n_clusters=0):
    data = df[field][df[field].str.len() > 0] 
    if n_clusters == 0:
        n_clusters = len(data)
    n_clusters = min(n_clusters, len(data))
    cn, ci = kmeans(data, n_clusters=100)
    print("here")