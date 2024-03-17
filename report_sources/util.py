from datetime import datetime
from decimal import *
import re

def isInt(value):
	try:
		x = int(value)
		return True
	except ValueError:
		return False

def isFloat(value):
	try:
		x = float(value)
		return True
	except ValueError:
		return False

def extract_datetime_Ymd(text, split_idx = -1):
    if split_idx!=-1:
        text = text.split(" ")[split_idx]
    return datetime.strptime(text, "%Y/%m/%d").date()

def extract_datetime_mdY(text, split_idx = -1):
    if split_idx!=-1:
        text = text.split(" ")[split_idx]
    return datetime.strptime(text, "%m/%d/%Y").date()

def extract_datetime_mov(text):
    return datetime.strptime(text, "%m.%d").date()

def extract_decimals_from_lines(lines, line_number):
    res = extract_decimals(lines(line_number))
    if res is None:
        res = extract_decimals(lines(line_number, offset=1))
    return res

def extract_decimals(text, join=False):
    p = '-?[\d]+[.,\d]+|[\d]+[. \d]+|[\d]*[.][\d]+|[\d]+'
    res = list(re.finditer(p, text))
    if not res:
          return None
    if len(res)>1:
        if join:
              return Decimal(''.join([f[0].replace(' ','').replace(',','') for f in res]))
        else:
            return [Decimal(f[0].replace(' ','').replace(',','')) for f in res]
    return Decimal(res[0][0].replace(' ','').replace(',',''))