from data.bank import Movement
import calendar
import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

TAG_SPLITTER = ','
TAGS_FIELD = 'tags'
INTERNAL_FIELD = 'internal'

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
    new_empty_n = max(0, n - t.shape[0])
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
        cd.add_record(bank, account, entry['date'], entry['value'], entry['desc'])

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

def set_mask(data, selected_data, mask=True, accumulate=False):
    if accumulate:
        prev_mask = (data['mask']==True)
    data.loc[data.index,'mask'] = False
    if accumulate:
        data.loc[((prev_mask) & (selected_data)), 'mask'] = mask
    else:
        data.loc[selected_data, 'mask'] = mask

def set_internal_mask(data, internal_mask_value=True, mask=True, accumulate=False):
    if internal_mask_value == 1: # non-internal only
        set_mask(data, data['internal'] == False, mask=mask, accumulate=accumulate)
    elif internal_mask_value == 2: # internal only
        set_mask(data, data['internal'] == True, mask=mask, accumulate=accumulate)
    else: # all
        data.loc[data.index,'mask'] = mask
        

def set_tag_mask(data, tag, mask=True, accumulate=False):
    if tag and tag[0]=='~':
        set_mask(data, col_not_contains_tag(data[TAGS_FIELD], tag[1:]), mask=mask, accumulate=accumulate)
    else:
        set_mask(data, col_contains_tag(data[TAGS_FIELD], tag), mask=mask, accumulate=accumulate)

def set_date_mask(data, year, month, mask=True, accumulate=False):
    set_mask(data, (data['year'] == year) & (data['month'] == month), mask=mask, accumulate=accumulate)


def append_tag(rec, tag):
    current_tags = rec.tags
    if current_tags is None or current_tags == '':
        next_splitter = ''
        current_tags = ''

    if tag is not None and tag != '':    
        split_new_tags = tag.split(TAG_SPLITTER)
        split_curr_tags = rec.tags.split(TAG_SPLITTER)
        for tag in split_new_tags:    
            if tag not in split_curr_tags:
                current_tags += next_splitter + tag
                next_splitter = TAG_SPLITTER
    
    return current_tags
    

def col_contains_tag(col, tag):
    return col.apply(lambda x: 
                  ((TAG_SPLITTER not in x) and 
                    x == tag) or
                  tag in x.split(TAG_SPLITTER))

def col_not_contains_tag(col, tag):
    return col.apply(lambda x: 
                     ((TAG_SPLITTER not in x) and 
                      x != tag) or 
                      tag not in x.split(TAG_SPLITTER))

def contains_tag(rec, tag):
    return ((TAG_SPLITTER not in rec.tags) and 
            rec.tags == tag) or \
        any(tag == t for t in rec.tags.split(TAG_SPLITTER))

def kmeans(data, **kwargs):
    tfidf = TfidfVectorizer()
    vec = tfidf.fit_transform(data.to_list())
    kmeans = KMeans(**kwargs)
    kmeans.fit(vec)
    sse = kmeans.inertia_
    clusters = kmeans.predict(vec)
    unique_clusters, cluster_description_indices = np.unique(clusters, return_index=True)
    cluster_indices = [np.where(clusters==i)[0] for i in unique_clusters]
    cluster_descriptions = []
    for idxs in cluster_indices:
        cluster_desc_vec = tfidf.transform(data.iloc[idxs].to_list()).toarray()
        # get common features across cluster entries
        all_common_features = tfidf.get_feature_names_out()[np.nonzero(np.prod(cluster_desc_vec,axis=0))[0]]
        # remove feature names starting or ending with numbers
        common_features = [f for f in all_common_features if not (f[0].isdigit() or f[-1].isdigit())]
        if len(common_features) == 0:
            common_features = all_common_features
        cluster_desc = ' '.join(common_features)
        cluster_descriptions.append(cluster_desc)
    final_cn = ['']
    final_ci = [[]]
    for i in range(len(cluster_descriptions)):
        if cluster_descriptions[i].strip() =='':
            final_ci[0].extend(cluster_indices[i])
        else:
            final_cn.append(cluster_descriptions[i])
            final_ci.append(cluster_indices[i])
    return final_cn, final_ci

def cluster(df, field, n_clusters=0):
    mask = (df['tags']=='') & (df[field]!='')
    reindex = []
    for i in range(len(mask)):
        if mask.iloc[i]:
            reindex.append(i)
    reindex = np.array(reindex)
    data = df[(df['tags']=='') & (df[field]!='')][field]
    if n_clusters == 0:
        n_clusters = len(data)
    n_clusters = min(100, min(n_clusters, len(data)))
    cn, ci = kmeans(data, n_clusters=n_clusters)
    remap_ci = []
    for kci in ci:
        remap_ci.append(reindex[kci])
    ci = remap_ci

    print(f"Computed KMeans Clustering for {n_clusters} clusters.")
    return cn, ci