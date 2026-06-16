"""Deeper checks: orphans, RM reconciliation, NON-SIP installment, date ranges, CIF<->name mapping."""
import pandas as pd
import numpy as np

CORE = "raw/Apex_Core_Database.xlsx"
LEDGER = "raw/Apex_Transaction_Ledger.xlsx"

master = pd.read_excel(CORE, sheet_name="Master File")
rmlist = pd.read_excel(CORE, sheet_name="RM List")
ledger = pd.read_excel(LEDGER, sheet_name="Transection")

reg = set(master["Registration No"].astype(str))
acc = set(ledger["Account Number"].astype(str))
orphans = acc - reg
print("Orphan ledger accounts (in ledger, not master):", len(orphans), sorted(orphans))
print("Master accounts with NO ledger rows:", len(reg - acc))
print("Sample master-no-ledger:", sorted(list(reg - acc))[:10])

# NON-SIP installment check
nonsip = master[master["Investment Type"] == "NON SIP"]
print("\nNON SIP rows:", len(nonsip), "| Current Installment != 0:", (nonsip["Current Installment Amount"] != 0).sum())
sip = master[master["Investment Type"] == "SIP"]
print("SIP rows:", len(sip), "| Current Installment == 0:", (sip["Current Installment Amount"] == 0).sum())

# Age outliers
age = master["Age"]
print("\nAge: nulls", age.isna().sum(), "| <18:", (age < 18).sum(), "| >100:", (age > 100).sum(), "| min", age.min(), "max", age.max())

# RM reconciliation
rm_names = set(rmlist["Introducer RM Name"].str.strip())
print("\nRM List names (16):", len(rm_names))
svc_names = set(master["Service RM Name"].dropna().str.strip())
intro_names = set(master["Introducer RM Name"].dropna().str.strip())
print("Service RM names in master not in RM List:", sorted(svc_names - rm_names))
print("Introducer RM names in master not in RM List (count):", len(intro_names - rm_names))
print("RM List names never appearing as Service RM:", sorted(rm_names - svc_names))
print("RM List names never appearing as Introducer:", sorted(rm_names - intro_names))

# CIF <-> name consistency
print("\nService RM CIF unique:", master["Service RM CIF"].nunique(), "| Service RM Name unique:", master["Service RM Name"].nunique())
# map service CIF -> set of names
svc_map = master.dropna(subset=["Service RM CIF"]).groupby("Service RM CIF")["Service RM Name"].nunique()
print("Service CIFs mapping to >1 name:", (svc_map > 1).sum())
svc_name_map = master.dropna(subset=["Service RM Name"]).groupby("Service RM Name")["Service RM CIF"].nunique()
print("Service Names mapping to >1 CIF:", (svc_name_map > 1).sum())
print("Service CIF nulls:", master["Service RM CIF"].isna().sum())

# Introducer CIF nulls vs name
print("\nIntroducer RM CIF nulls:", master["Introducer RM CIF"].isna().sum())
print("Introducer RM Name nulls:", master["Introducer RM Name"].isna().sum())
# Where Introducer CIF null, is name present?
nullcif = master[master["Introducer RM CIF"].isna()]
print("Rows w/ null Introducer CIF but non-null name:", nullcif["Introducer RM Name"].notna().sum())
print("Sample introducer names where CIF null:", nullcif["Introducer RM Name"].dropna().unique()[:10])

# Onboarding Department
print("\nOnboarding Department:", master["Onboarding Department"].value_counts(dropna=False).to_dict())

# Date range of ledger
ld = pd.to_datetime(ledger["Purchase/Surrender Date"], errors="coerce")
print("\nLedger date range:", ld.min(), "->", ld.max(), "| parse nulls:", ld.isna().sum())
fpd = pd.to_datetime(master["First Purchase Date"], errors="coerce")
print("First Purchase Date range:", fpd.min(), "->", fpd.max(), "| parse nulls:", fpd.isna().sum())

# transaction totals by type
print("\nLedger Total by type:")
print(ledger.groupby("Type of Transaction")["Total"].sum())

# Tenor distribution for NON SIP
print("\nTenor==0 count:", (master["Tenor In Month"] == 0).sum(), "by type:")
print(master.groupby("Investment Type")["Tenor In Month"].apply(lambda s: (s==0).sum()))

# Customer No vs Mobile relationship
cm = master.groupby("Mobile No")["Customer No."].nunique()
print("\nMobiles mapping to >1 Customer No.:", (cm > 1).sum())
mc = master.groupby("Customer No.")["Mobile No"].nunique()
print("Customer No. mapping to >1 Mobile:", (mc > 1).sum())
