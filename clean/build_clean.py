"""
Agent 1 — Data Engineering pipeline for Apex Asset Management case study.
Turns raw source files into clean, joined, analysis-ready tables + reports.

Reads rules from definitions.yaml (single source of truth). Does NO analysis.
Run:  .venv/Scripts/python.exe clean/build_clean.py
Reproducible: random_seed=42.
"""
import os
import sys
import yaml
import numpy as np
import pandas as pd
from datetime import datetime

SEED = 42
np.random.seed(SEED)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")
CLEAN = os.path.join(ROOT, "clean")
os.makedirs(CLEAN, exist_ok=True)

with open(os.path.join(ROOT, "definitions.yaml"), "r", encoding="utf-8") as f:
    DEFS = yaml.safe_load(f)

AS_OF = pd.Timestamp(DEFS["project"]["as_of_date"])  # 2026-05-31
SENTINELS = DEFS["null_sentinels"]
RAW2CANON = DEFS["status"]["raw_to_canonical"]
CHURN_STRICT = set(DEFS["status"]["churn_strict"]["members"])
CHURN_BROAD = set(DEFS["status"]["churn_broad"]["members"])
EXCLUDE_RATES = set(DEFS["status"]["exclude_from_rates"]["members"])
AGE_QF = DEFS["bands"]["age_quality_flag"]

CORE = os.path.join(RAW, DEFS["source_files"]["core_db"])
LEDGER = os.path.join(RAW, DEFS["source_files"]["ledger"])

LOG = []  # conservation log: (step, rows_in, rows_out, note)


def logstep(step, rin, rout, note=""):
    LOG.append((step, rin, rout, note))
    print(f"[STEP] {step}: in={rin} out={rout} {note}")


def clean_sentinels(s):
    """Replace sentinel strings with NaN. Handles ' ', '', '00:00:00', '1900-01-01'."""
    out = s.copy()
    if out.dtype == object:
        stripped = out.astype(str).str.strip()
        mask = stripped.isin([str(x).strip() for x in SENTINELS]) | (stripped == "") | (stripped == "nan") | (stripped == "NaT")
        # also catch any value that begins with the 1900-01-01 epoch sentinel
        mask = mask | stripped.str.startswith("1900-01-01")
        out = out.where(~mask, np.nan)
    return out


def parse_date(s):
    """Clean sentinels then parse to datetime (date precision)."""
    c = clean_sentinels(s)
    return pd.to_datetime(c, errors="coerce")


def months_between(later, earlier):
    """Whole-month difference (calendar-month based), float NaN-safe."""
    res = (later.dt.year - earlier.dt.year) * 12 + (later.dt.month - earlier.dt.month)
    return res.astype("Float64")


def band_apply(value, bands, label_key="label"):
    """Left-closed [min,max) banding from definitions bands list. Returns label or NA."""
    if pd.isna(value):
        return pd.NA
    for b in bands:
        if b["min"] <= value < b["max"]:
            return b[label_key]
    return pd.NA


# =====================================================================
# LOAD
# =====================================================================
print("=" * 70)
print("LOADING RAW")
master = pd.read_excel(CORE, sheet_name="Master File")
rmlist = pd.read_excel(CORE, sheet_name="RM List")
ledger = pd.read_excel(LEDGER, sheet_name="Transection")
logstep("load master", len(master), len(master))
logstep("load rmlist", len(rmlist), len(rmlist))
logstep("load ledger", len(ledger), len(ledger))

REPORT = {}  # profiling / flag counts collected for the data quality report

# =====================================================================
# RM LIST + CANONICAL RM IDENTITY
# =====================================================================
rmlist = rmlist[["Introducer RM Name"]].copy()
rmlist["Introducer RM Name"] = rmlist["Introducer RM Name"].astype(str).str.strip()
rmlist = rmlist.dropna().drop_duplicates().reset_index(drop=True)
official_rm_names = set(rmlist["Introducer RM Name"])
REPORT["rm_list_count"] = len(official_rm_names)

# Build canonical CIF -> name map from ALL master sources (service + introducer).
# Verified 1:1 (42 distinct CIFs, no CIF maps to >1 name).
def _pairs(cif_col, name_col):
    d = master[[cif_col, name_col]].copy()
    d.columns = ["cif", "name"]
    d = d.dropna(subset=["cif"])
    d["name"] = d["name"].astype(str).str.strip()
    d["cif"] = d["cif"].astype("Int64")
    return d.drop_duplicates()

cif_pairs = pd.concat([
    _pairs("Service RM CIF", "Service RM Name"),
    _pairs("Introducer RM CIF", "Introducer RM Name"),
]).drop_duplicates()
cif_to_name = dict(zip(cif_pairs["cif"], cif_pairs["name"]))
name_to_cif = dict(zip(cif_pairs["name"], cif_pairs["cif"]))
REPORT["distinct_rm_cifs"] = cif_pairs["cif"].nunique()
REPORT["cifs_multi_name"] = int((cif_pairs.groupby("cif")["name"].nunique() > 1).sum())

# =====================================================================
# ACCOUNTS_CLEAN
# =====================================================================
print("=" * 70)
print("BUILDING accounts_clean")
ac = master.copy()

# --- string keys ---
ac["registration_no"] = ac["Registration No"].astype(str).str.strip()
ac["fund"] = ac["Fund"].astype(str).str.strip()
ac["investment_type"] = ac["Investment Type"].astype(str).str.strip()  # 'SIP' / 'NON SIP'
ac["is_sip"] = ac["investment_type"].eq("SIP")
ac["customer_no"] = ac["Customer No."].astype("Int64")
ac["mobile_no"] = ac["Mobile No"].astype(str).str.strip()
ac["customer_name"] = ac["Customer Name"].astype(str).str.strip()

# --- status / churn ---
ac["activity_status_raw"] = ac["Activity Status"].astype(str).str.strip()
ac["status"] = ac["activity_status_raw"].map(RAW2CANON)
ac["churn_strict"] = ac["status"].isin(CHURN_STRICT)
ac["churn_broad"] = ac["status"].isin(CHURN_BROAD)
ac["is_active"] = ac["status"].isin(set(DEFS["status"]["active_members"]))
ac["excluded_from_rates"] = ac["status"].isin(EXCLUDE_RATES)  # suspended

# --- numerics ---
ac["age"] = pd.to_numeric(clean_sentinels(ac["Age"]), errors="coerce")
ac["onboarding_amount"] = pd.to_numeric(clean_sentinels(ac["Amount (While onboarding)"]), errors="coerce")
ac["current_installment_amount"] = pd.to_numeric(clean_sentinels(ac["Current Installment Amount"]), errors="coerce")
ac["tenor_in_month"] = pd.to_numeric(clean_sentinels(ac["Tenor In Month"]), errors="coerce")
ac["investment_value_market"] = pd.to_numeric(clean_sentinels(ac["Investment Value (At Market)"]), errors="coerce")

# --- dates ---
ac["first_purchase_date"] = parse_date(ac["First Purchase Date"])
ac["tenure_maturity_date"] = parse_date(ac["Tenure Maturity Date"])
ac["account_closing_date"] = parse_date(ac["Account Closing Date"])
ac["sip_discontinuation_date"] = parse_date(ac["SIP Discontinuation Date"])

# --- derived date fields ---
ac["onboarding_month"] = ac["first_purchase_date"].dt.to_period("M").astype(str)
ac["onboarding_month"] = ac["onboarding_month"].replace("NaT", pd.NA)
ac["onboarding_year"] = ac["first_purchase_date"].dt.year.astype("Int64")
# tenure to date: months from first purchase to as_of (or closing if closed earlier)
end_for_tenure = ac["account_closing_date"].fillna(AS_OF)
end_for_tenure = end_for_tenure.where(end_for_tenure <= AS_OF, AS_OF)
ac["tenure_to_date_months"] = months_between(end_for_tenure, ac["first_purchase_date"])
ac["days_to_closure"] = (ac["account_closing_date"] - ac["first_purchase_date"]).dt.days.astype("Int64")
ac["days_to_discontinuation"] = (ac["sip_discontinuation_date"] - ac["first_purchase_date"]).dt.days.astype("Int64")

# --- RM attribution (acquisition = introducer; servicing = service) ---
ac["introducer_rm_name"] = ac["Introducer RM Name"].astype(str).str.strip()
ac["introducer_rm_cif"] = ac["Introducer RM CIF"].astype("Int64")
ac["service_rm_name"] = ac["Service RM Name"].astype(str).str.strip()
ac["service_rm_cif"] = ac["Service RM CIF"].astype("Int64")
# canonical name from CIF where available, else keep raw trimmed name
ac["introducer_rm_name_canon"] = ac["introducer_rm_cif"].map(cif_to_name).fillna(ac["introducer_rm_name"])
ac["service_rm_name_canon"] = ac["service_rm_cif"].map(cif_to_name).fillna(ac["service_rm_name"])
ac["onboarding_department"] = clean_sentinels(ac["Onboarding Department"])

# reconciliation flags
ac["introducer_in_rmlist"] = ac["introducer_rm_name"].isin(official_rm_names)
ac["service_in_rmlist"] = ac["service_rm_name"].isin(official_rm_names)
ac["introducer_cif_missing"] = ac["introducer_rm_cif"].isna()
ac["service_cif_missing"] = ac["service_rm_cif"].isna()

# --- data quality flags (flag, never drop) ---
ac["flag_age_missing"] = ac["age"].isna()
ac["flag_age_out_of_range"] = ac["age"].notna() & ((ac["age"] < AGE_QF["min_valid"]) | (ac["age"] > AGE_QF["max_valid"]))
ac["flag_age_invalid"] = ac["flag_age_missing"] | ac["flag_age_out_of_range"]
ac["flag_nonsip_installment_nonzero"] = (~ac["is_sip"]) & (ac["current_installment_amount"].fillna(0) != 0)
ac["flag_sip_tenor_zero"] = ac["is_sip"] & (ac["tenor_in_month"].fillna(-1) == 0)
ac["flag_closed_no_closing_date"] = (ac["status"] == "closed") & ac["account_closing_date"].isna()
ac["flag_disc_no_disc_date"] = (ac["status"] == "discontinued") & ac["sip_discontinuation_date"].isna()

# --- band columns ---
ac["age_group"] = ac["age"].apply(lambda v: band_apply(v, DEFS["bands"]["age_groups"]))
# installment band only meaningful for SIP (NON SIP installment == 0)
ac["installment_band"] = ac.apply(
    lambda r: band_apply(r["current_installment_amount"], DEFS["bands"]["installment_bands_sip"]) if r["is_sip"] else pd.NA,
    axis=1,
)
ac["tenor_band"] = ac["tenor_in_month"].apply(lambda v: band_apply(v, DEFS["bands"]["tenor_bands_months"]))

ACCOUNT_COLS = [
    "registration_no", "fund", "investment_type", "is_sip",
    "customer_no", "mobile_no", "customer_name",
    "activity_status_raw", "status", "churn_strict", "churn_broad", "is_active", "excluded_from_rates",
    "age", "onboarding_amount", "current_installment_amount", "tenor_in_month", "investment_value_market",
    "first_purchase_date", "tenure_maturity_date", "account_closing_date", "sip_discontinuation_date",
    "onboarding_month", "onboarding_year", "tenure_to_date_months", "days_to_closure", "days_to_discontinuation",
    "introducer_rm_name", "introducer_rm_name_canon", "introducer_rm_cif",
    "service_rm_name", "service_rm_name_canon", "service_rm_cif", "onboarding_department",
    "introducer_in_rmlist", "service_in_rmlist", "introducer_cif_missing", "service_cif_missing",
    "age_group", "installment_band", "tenor_band",
    "flag_age_missing", "flag_age_out_of_range", "flag_age_invalid",
    "flag_nonsip_installment_nonzero", "flag_sip_tenor_zero",
    "flag_closed_no_closing_date", "flag_disc_no_disc_date",
]
accounts_clean = ac[ACCOUNT_COLS].copy()
logstep("accounts_clean", len(master), len(accounts_clean), "one row per account")

# =====================================================================
# RM_ATTRIBUTION
# =====================================================================
rm_attribution = accounts_clean[[
    "registration_no",
    "introducer_rm_name", "introducer_rm_name_canon", "introducer_rm_cif", "introducer_in_rmlist",
    "service_rm_name", "service_rm_name_canon", "service_rm_cif", "service_in_rmlist",
]].copy()
logstep("rm_attribution", len(accounts_clean), len(rm_attribution))

# =====================================================================
# TRANSACTIONS_CLEAN  (+ orphan quarantine)
# =====================================================================
print("=" * 70)
print("BUILDING transactions_clean")
tx = ledger.copy()
tx["account_number"] = tx["Account Number"].astype(str).str.strip()
tx["customer_name_ledger"] = tx["Customer Name"].astype(str).str.strip()
tx["transaction_type"] = tx["Type of Transaction"].astype(str).str.strip()
tx["amount"] = pd.to_numeric(clean_sentinels(tx["Total"]), errors="coerce")
tx["transaction_date"] = parse_date(tx["Purchase/Surrender Date"])
tx["transaction_month"] = tx["transaction_date"].dt.to_period("M").astype(str)

reg_set = set(accounts_clean["registration_no"])
orphan_mask = ~tx["account_number"].isin(reg_set)
orphans = tx[orphan_mask].copy()
orphan_accounts = sorted(orphans["account_number"].unique())
REPORT["orphan_accounts"] = orphan_accounts
REPORT["orphan_rows"] = int(orphan_mask.sum())

orphans_out = orphans[["account_number", "customer_name_ledger", "transaction_type", "amount", "transaction_date"]].copy()
orphans_out.to_csv(os.path.join(CLEAN, "orphans.csv"), index=False)
logstep("ledger orphan quarantine", len(tx), int(orphan_mask.sum()), f"orphan accts={orphan_accounts}")

tx_main = tx[~orphan_mask].copy()
logstep("transactions after orphan removal", len(tx), len(tx_main))

# join fund + RM attribution from master
join_cols = accounts_clean[["registration_no", "fund", "investment_type",
                            "introducer_rm_name_canon", "introducer_rm_cif",
                            "service_rm_name_canon", "service_rm_cif", "status"]].rename(
    columns={"registration_no": "account_number"})
tx_main = tx_main.merge(join_cols, on="account_number", how="left")
assert tx_main["fund"].isna().sum() == 0, "join produced unmatched tx rows"
logstep("transactions join master", len(tx_main), len(tx_main), "all matched to fund/RM")

TX_COLS = [
    "account_number", "customer_name_ledger", "transaction_type", "amount",
    "transaction_date", "transaction_month",
    "fund", "investment_type", "status",
    "introducer_rm_name_canon", "introducer_rm_cif",
    "service_rm_name_canon", "service_rm_cif",
]
transactions_clean = tx_main[TX_COLS].copy()

# =====================================================================
# MONTHLY_FLOWS  (account x calendar-month: purchase / surrender / dividend)
# =====================================================================
print("=" * 70)
print("BUILDING monthly_flows")
pivot = transactions_clean.pivot_table(
    index=["account_number", "transaction_month"],
    columns="transaction_type",
    values="amount",
    aggfunc="sum",
    fill_value=0.0,
).reset_index()
pivot.columns.name = None
for t in ["Purchase", "Surrender", "Dividend"]:
    if t not in pivot.columns:
        pivot[t] = 0.0
monthly_flows = pivot.rename(columns={
    "Purchase": "purchase_amount",
    "Surrender": "surrender_amount",
    "Dividend": "dividend_amount",
})
monthly_flows["net_flow"] = monthly_flows["purchase_amount"] - monthly_flows["surrender_amount"]
# attach fund + status for downstream cohort work
monthly_flows = monthly_flows.merge(
    accounts_clean[["registration_no", "fund", "investment_type", "status",
                    "service_rm_name_canon", "onboarding_month"]].rename(columns={"registration_no": "account_number"}),
    on="account_number", how="left")
monthly_flows = monthly_flows[[
    "account_number", "transaction_month", "purchase_amount", "surrender_amount",
    "dividend_amount", "net_flow", "fund", "investment_type", "status",
    "service_rm_name_canon", "onboarding_month",
]]
logstep("monthly_flows", len(transactions_clean), len(monthly_flows), "account x month grain")

# reconciliation check
recon = {
    "Purchase": (transactions_clean.loc[transactions_clean.transaction_type == "Purchase", "amount"].sum(),
                 monthly_flows["purchase_amount"].sum()),
    "Surrender": (transactions_clean.loc[transactions_clean.transaction_type == "Surrender", "amount"].sum(),
                  monthly_flows["surrender_amount"].sum()),
    "Dividend": (transactions_clean.loc[transactions_clean.transaction_type == "Dividend", "amount"].sum(),
                 monthly_flows["dividend_amount"].sum()),
}
REPORT["recon"] = recon
for k, (a, b) in recon.items():
    assert abs(a - b) < 1.0, f"recon mismatch {k}: {a} vs {b}"
    print(f"[RECON] {k}: tx={a:,.2f}  monthly={b:,.2f}  OK")

# =====================================================================
# CUSTOMERS  (rolled up to Mobile)
# =====================================================================
print("=" * 70)
print("BUILDING customers")
g = accounts_clean.groupby("mobile_no")
customers = pd.DataFrame({
    "mobile_no": g.size().index,
    "accounts_per_customer": g.size().values,
})
agg = accounts_clean.groupby("mobile_no").agg(
    customer_name=("customer_name", "first"),
    customer_no_primary=("customer_no", "first"),
    funds_held=("fund", lambda s: s.nunique()),
    total_aum_market=("investment_value_market", "sum"),
    total_onboarding_amount=("onboarding_amount", "sum"),
    total_current_installment=("current_installment_amount", "sum"),
    first_onboarding_date=("first_purchase_date", "min"),
    last_onboarding_date=("first_purchase_date", "max"),
    n_active_accounts=("is_active", "sum"),
    n_churn_strict_accounts=("churn_strict", "sum"),
    n_sip_accounts=("is_sip", "sum"),
).reset_index()
customers = customers.merge(agg, on="mobile_no", how="left")
customers["first_onboarding_month"] = customers["first_onboarding_date"].dt.to_period("M").astype(str).replace("NaT", pd.NA)
customers["last_onboarding_month"] = customers["last_onboarding_date"].dt.to_period("M").astype(str).replace("NaT", pd.NA)
customers["is_multi_account"] = customers["accounts_per_customer"] > 1
logstep("customers", len(accounts_clean), len(customers), "rolled to Mobile")
REPORT["multi_account_customers"] = int((customers["accounts_per_customer"] > 1).sum())

# =====================================================================
# WRITE OUTPUTS (parquet + csv)
# =====================================================================
print("=" * 70)
print("WRITING OUTPUTS")
def write_both(df, name):
    p = os.path.join(CLEAN, name + ".parquet")
    c = os.path.join(CLEAN, name + ".csv")
    df.to_parquet(p, index=False)
    df.to_csv(c, index=False)
    print(f"  wrote {name}: {df.shape} -> parquet + csv")

write_both(accounts_clean, "accounts_clean")
write_both(customers, "customers")
write_both(transactions_clean, "transactions_clean")
write_both(monthly_flows, "monthly_flows")
write_both(rm_attribution, "rm_attribution")
# orphans.csv already written

# =====================================================================
# COLLECT REPORT NUMBERS
# =====================================================================
REPORT["registration_no_unique"] = int(accounts_clean["registration_no"].nunique())
REPORT["registration_no_rows"] = int(len(accounts_clean))
REPORT["mobile_unique"] = int(accounts_clean["mobile_no"].nunique())
REPORT["customer_no_unique"] = int(accounts_clean["customer_no"].nunique())
REPORT["status_counts"] = accounts_clean["status"].value_counts().to_dict()
REPORT["status_sum"] = int(accounts_clean["status"].value_counts().sum())
REPORT["churn_strict_count"] = int(accounts_clean["churn_strict"].sum())
REPORT["churn_broad_count"] = int(accounts_clean["churn_broad"].sum())
REPORT["flag_age_missing"] = int(accounts_clean["flag_age_missing"].sum())
REPORT["flag_age_out_of_range"] = int(accounts_clean["flag_age_out_of_range"].sum())
REPORT["flag_age_invalid"] = int(accounts_clean["flag_age_invalid"].sum())
REPORT["flag_nonsip_installment_nonzero"] = int(accounts_clean["flag_nonsip_installment_nonzero"].sum())
REPORT["flag_sip_tenor_zero"] = int(accounts_clean["flag_sip_tenor_zero"].sum())
REPORT["flag_closed_no_closing_date"] = int(accounts_clean["flag_closed_no_closing_date"].sum())
REPORT["flag_disc_no_disc_date"] = int(accounts_clean["flag_disc_no_disc_date"].sum())
REPORT["service_names_not_in_rmlist"] = sorted(set(accounts_clean.loc[~accounts_clean["service_in_rmlist"], "service_rm_name"]))
REPORT["n_introducer_names_not_in_rmlist"] = int(accounts_clean.loc[~accounts_clean["introducer_in_rmlist"], "introducer_rm_name"].nunique())
REPORT["introducer_cif_missing_rows"] = int(accounts_clean["introducer_cif_missing"].sum())
REPORT["service_cif_missing_rows"] = int(accounts_clean["service_cif_missing"].sum())
REPORT["onboarding_dept_null"] = int(accounts_clean["onboarding_department"].isna().sum())

# sentinel cleaning evidence: confirm no sentinels remain in date/amount cols
def residual_sentinels(df, cols):
    out = {}
    for c in cols:
        s = df[c].astype(str)
        bad = s.isin(["00:00:00", "1900-01-01", " "]) | s.str.startswith("1900-01-01")
        out[c] = int(bad.sum())
    return out
REPORT["residual_sentinels"] = residual_sentinels(
    accounts_clean,
    ["first_purchase_date", "tenure_maturity_date", "account_closing_date",
     "sip_discontinuation_date", "age", "onboarding_amount", "current_installment_amount"])

# date ordering validation
def cnt(mask):
    return int(mask.sum())
fpd = accounts_clean["first_purchase_date"]
acd = accounts_clean["account_closing_date"]
sdd = accounts_clean["sip_discontinuation_date"]
tmd = accounts_clean["tenure_maturity_date"]
REPORT["viol_fpd_gt_closing"] = cnt(acd.notna() & (fpd > acd))
REPORT["viol_fpd_gt_disc"] = cnt(sdd.notna() & (fpd > sdd))
REPORT["viol_fpd_gt_asof"] = cnt(fpd.notna() & (fpd > AS_OF))
REPORT["viol_closing_gt_asof"] = cnt(acd.notna() & (acd > AS_OF))
REPORT["viol_disc_gt_asof"] = cnt(sdd.notna() & (sdd > AS_OF))
REPORT["viol_tmd_lt_fpd"] = cnt(tmd.notna() & fpd.notna() & (tmd < fpd))

import json
with open(os.path.join(CLEAN, "_report_numbers.json"), "w", encoding="utf-8") as f:
    json.dump({k: (v if not isinstance(v, dict) else {str(kk): vv for kk, vv in v.items()})
               for k, v in REPORT.items()}, f, indent=2, default=str)

# conservation log
with open(os.path.join(CLEAN, "_conservation_log.txt"), "w", encoding="utf-8") as f:
    for step, rin, rout, note in LOG:
        f.write(f"{step}: in={rin} out={rout} {note}\n")

print("=" * 70)
print("DONE. Key numbers:")
for k in ["registration_no_unique", "mobile_unique", "multi_account_customers",
          "orphan_rows", "status_sum", "churn_strict_count", "churn_broad_count"]:
    print(f"  {k}: {REPORT[k]}")
print("status_counts:", REPORT["status_counts"])
