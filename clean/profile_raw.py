"""Profile raw source sheets: shapes, dtypes, null/sentinel rates, unique key counts."""
import pandas as pd
import numpy as np

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)

CORE = "raw/Apex_Core_Database.xlsx"
LEDGER = "raw/Apex_Transaction_Ledger.xlsx"
SENTINELS = [" ", "", "00:00:00", "1900-01-01"]


def sentinel_rate(s):
    raw = s.astype(str).str.strip()
    # count common sentinels
    is_sent = s.isna() | s.astype(str).isin(SENTINELS) | (raw == "") | (raw == "00:00:00") | (raw == "1900-01-01") | raw.str.startswith("1900-01-01")
    return is_sent.sum()


def profile(df, name):
    print("=" * 80)
    print(f"SHEET: {name}  shape={df.shape}")
    print("-" * 80)
    for c in df.columns:
        s = df[c]
        nnull = s.isna().sum()
        sent = sentinel_rate(s)
        nun = s.nunique(dropna=True)
        sample = s.dropna().astype(str).unique()[:4]
        print(f"  {c!r:42} dtype={str(s.dtype):10} nulls={nnull:6} sentinel~={sent:6} nuniq={nun:7} ex={list(sample)}")
    print()


xl = pd.ExcelFile(CORE)
print("CORE sheets:", xl.sheet_names)
master = pd.read_excel(CORE, sheet_name="Master File")
rmlist = pd.read_excel(CORE, sheet_name="RM List")
profile(master, "Master File")
profile(rmlist, "RM List")

xl2 = pd.ExcelFile(LEDGER)
print("LEDGER sheets:", xl2.sheet_names)
ledger = pd.read_excel(LEDGER, sheet_name=xl2.sheet_names[0])
profile(ledger, xl2.sheet_names[0])

print("=" * 80)
print("KEY CHECKS")
print("Registration No nunique:", master["Registration No"].nunique(), "rows:", len(master))
print("Registration No dup count:", master["Registration No"].duplicated().sum())
mob_col = [c for c in master.columns if "Mobile" in c]
print("Mobile col:", mob_col)
if mob_col:
    mc = mob_col[0]
    print("Mobile nunique:", master[mc].nunique(), "nulls:", master[mc].isna().sum())
    vc = master.groupby(mc).size()
    print("Customers with >1 account (multi):", (vc > 1).sum())
cust_col = [c for c in master.columns if "Customer No" in c]
print("Customer No col:", cust_col)
if cust_col:
    print("Customer No nunique:", master[cust_col[0]].nunique())

print("\nActivity Status value_counts:")
st_col = [c for c in master.columns if "Status" in c]
print("status col:", st_col)
if st_col:
    print(master[st_col[0]].value_counts(dropna=False))

print("\nInvestment Type / Type counts:")
for c in master.columns:
    if "Type" in c or "SIP" in c.upper():
        print(c, "->", master[c].value_counts(dropna=False).to_dict())

print("\nLedger Type of Transaction counts:")
for c in ledger.columns:
    if "Type" in c:
        print(c, "->", ledger[c].value_counts(dropna=False).to_dict())

print("\nLedger columns:", list(ledger.columns))
print("Master columns:", list(master.columns))
print("RM List columns:", list(rmlist.columns))
print("\nRM List head:")
print(rmlist.head(20).to_string())
