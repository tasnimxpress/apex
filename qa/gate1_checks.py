"""
GATE 1 QA — Apex Asset Management case study.
Principle: REPRODUCE, DON'T TRUST. Everything is recomputed from raw/ and
cross-checked against clean/. Agent 1's reported numbers are NOT used as inputs.

Run:  d:/GitHub/apex/.venv/Scripts/python.exe qa/gate1_checks.py
Writes evidence to stdout; the markdown report is authored from these results.
"""
import json
import numpy as np
import pandas as pd

ROOT = "d:/GitHub/apex"
AS_OF = pd.Timestamp("2026-05-31")
SENTINELS = [" ", "", "00:00:00", "1900-01-01"]

results = []  # (id, desc, status, evidence)

def chk(cid, desc, passed, evidence):
    results.append((cid, desc, "PASS" if passed else "FAIL", evidence))

# ---------------- RAW (independent recompute) ----------------
m = pd.read_excel(f"{ROOT}/raw/Apex_Core_Database.xlsx", sheet_name="Master File")
rl = pd.read_excel(f"{ROOT}/raw/Apex_Core_Database.xlsx", sheet_name="RM List")
led = pd.read_excel(f"{ROOT}/raw/Apex_Transaction_Ledger.xlsx", sheet_name="Transection")

n_master = len(m)
n_ledger = len(led)

# ---------------- CLEAN ----------------
ac = pd.read_parquet(f"{ROOT}/clean/accounts_clean.parquet")
tx = pd.read_parquet(f"{ROOT}/clean/transactions_clean.parquet")
mf = pd.read_parquet(f"{ROOT}/clean/monthly_flows.parquet")
cust = pd.read_parquet(f"{ROOT}/clean/customers.parquet")
orph = pd.read_csv(f"{ROOT}/clean/orphans.csv")

# ===== STRUCTURAL / INTEGRITY =====

# 1. Registration No unique == 12,229 (from RAW)
raw_reg_unique = m["Registration No"].nunique()
raw_reg_rows = len(m)
chk("S1", "Registration No unique == 12,229 (raw)",
    raw_reg_unique == 12229 and raw_reg_rows == 12229,
    f"raw rows={raw_reg_rows}, unique={raw_reg_unique}")
# clean side
chk("S1b", "accounts_clean registration_no unique == 12,229",
    ac["registration_no"].nunique() == 12229 and len(ac) == 12229,
    f"clean rows={len(ac)}, unique={ac['registration_no'].nunique()}")

# 2. Customer key (Mobile) unique ~8,570 and multi-account ~2,352 (from RAW)
raw_mobile_unique = m["Mobile No"].nunique()
mob_counts = m.groupby("Mobile No").size()
raw_multi = int((mob_counts > 1).sum())
chk("S2", "Mobile unique count ~8,570 (raw)",
    raw_mobile_unique == 8570,
    f"raw mobile unique={raw_mobile_unique}")
chk("S2b", "Multi-account customers ~2,352 (raw, mobiles with >1 account)",
    raw_multi == 2352,
    f"raw multi-account mobiles={raw_multi}")
# clean cross-check
clean_multi = int((cust["accounts_per_customer"] > 1).sum())
chk("S2c", "customers.parquet: rows==8,570 and is_multi_account==2,352",
    len(cust) == 8570 and clean_multi == 2352,
    f"customers rows={len(cust)}, multi(accounts_per_customer>1)={clean_multi}, "
    f"is_multi_account flag sum={int(cust['is_multi_account'].sum())}")

# 3. Join: exactly 3 orphan ledger accounts; 0 master accounts dropped (RAW recompute)
master_accts = set(m["Registration No"].astype(str))
ledger_accts = set(led["Account Number"].astype(str))
orphan_accts = sorted(ledger_accts - master_accts)
orphan_rows_raw = int(led["Account Number"].astype(str).isin(orphan_accts).sum())
chk("S3", "Exactly 3 orphan ledger accounts (raw set-diff)",
    len(orphan_accts) == 3,
    f"orphan accts={orphan_accts} (n={len(orphan_accts)}), orphan rows raw={orphan_rows_raw}")
# 0 master dropped: every master reg present in accounts_clean
master_dropped = master_accts - set(ac["registration_no"].astype(str))
chk("S3b", "0 master accounts dropped",
    len(master_dropped) == 0,
    f"master accounts missing from accounts_clean = {len(master_dropped)}")
# orphans.csv matches
orph_accts_file = sorted(set(orph["account_number"].astype(str)))
chk("S3c", "orphans.csv accounts == raw orphan set",
    orph_accts_file == orphan_accts,
    f"orphans.csv accts={orph_accts_file}, rows={len(orph)}")

# 4. Row counts conserved
# accounts_clean rows == master rows
chk("S4a", "accounts_clean rows == master rows",
    len(ac) == n_master, f"accounts_clean={len(ac)}, master={n_master}")
# transactions_clean + orphan rows == ledger rows
chk("S4b", "transactions_clean + orphan rows == ledger rows",
    len(tx) + orphan_rows_raw == n_ledger,
    f"transactions_clean={len(tx)} + orphan_rows={orphan_rows_raw} = "
    f"{len(tx)+orphan_rows_raw}; ledger={n_ledger}")

# 5. Status canonical counts sum to source totals
canon_map = {"Active":"active","Closed":"closed","Discontinue":"discontinued",
             "Inactive":"inactive","Suspended":"suspended"}
raw_status = m["Activity Status"].map(canon_map).value_counts().to_dict()
clean_status = ac["status"].value_counts().to_dict()
expected = {"active":6925,"closed":3500,"inactive":1124,"discontinued":678,"suspended":2}
status_match = all(raw_status.get(k)==v for k,v in expected.items()) and \
               all(clean_status.get(k)==v for k,v in expected.items())
status_sum_clean = sum(clean_status.values())
chk("S5", "Status canonical counts match & sum to 12,229",
    status_match and status_sum_clean == 12229,
    f"raw={raw_status}; clean={clean_status}; clean_sum={status_sum_clean}")

# 6. null_sentinels removed in date/amount cols (clean)
date_cols = ["first_purchase_date","tenure_maturity_date","account_closing_date","sip_discontinuation_date"]
amt_cols = ["age","onboarding_amount","current_installment_amount","investment_value_market","tenor_in_month"]
residual = {}
for c in date_cols + amt_cols:
    if c not in ac.columns:
        residual[c] = "MISSING_COL"; continue
    col = ac[c]
    # date cols should be datetime; amount cols numeric. Check for sentinel string residue & 1900 dates
    cnt = 0
    if pd.api.types.is_datetime64_any_dtype(col):
        cnt += int((col == pd.Timestamp("1900-01-01")).sum())
    else:
        s = col.astype(str).str.strip()
        cnt += int(s.isin([x.strip() for x in SENTINELS if x.strip()!=""]).sum())
        cnt += int((s == "00:00:00").sum()) + int((s == "1900-01-01").sum())
    residual[c] = cnt
tx_resid = 0
if pd.api.types.is_datetime64_any_dtype(tx["transaction_date"]):
    tx_resid = int((tx["transaction_date"] == pd.Timestamp("1900-01-01")).sum())
chk("S6", "No null_sentinels / 1900-01-01 left in date/amount cols",
    all(v == 0 for v in residual.values()) and tx_resid == 0,
    f"residuals={residual}; tx_date 1900 count={tx_resid}")

# ===== LOGIC =====

# 7. Date ordering on CLEAN (independent recompute)
fpd = ac["first_purchase_date"]
clo = ac["account_closing_date"]
dis = ac["sip_discontinuation_date"]
tmd = ac["tenure_maturity_date"]
closed_mask = ac["status"] == "closed"
disc_mask = ac["status"] == "discontinued"

v_fpd_close = int(((fpd > clo) & clo.notna() & fpd.notna() & closed_mask).sum())
v_fpd_disc  = int(((fpd > dis) & dis.notna() & fpd.notna() & disc_mask).sum())
v_fpd_asof  = int(((fpd > AS_OF) & fpd.notna()).sum())
v_close_asof= int(((clo > AS_OF) & clo.notna()).sum())
v_disc_asof = int(((dis > AS_OF) & dis.notna()).sum())
chk("L1", "FPD <= closing(where closed), <= disc(where discontinued), all <= as_of",
    v_fpd_close==0 and v_fpd_disc==0 and v_fpd_asof==0 and v_close_asof==0 and v_disc_asof==0,
    f"fpd>close={v_fpd_close}, fpd>disc={v_fpd_disc}, fpd>asof={v_fpd_asof}, "
    f"close>asof={v_close_asof}, disc>asof={v_disc_asof}")

# 8. Tenure Maturity Date >= First Purchase Date
v_tmd = int(((tmd < fpd) & tmd.notna() & fpd.notna()).sum())
chk("L2", "Tenure Maturity Date >= First Purchase Date",
    v_tmd == 0, f"tmd<fpd violations={v_tmd}")

# 9. Current Installment Amount == 0 for all Non-SIP rows (recompute from clean + raw)
nonsip = ac[ac["investment_type"].str.upper().str.replace(" ","")=="NONSIP"]
nonsip_nonzero = int((nonsip["current_installment_amount"].fillna(0) != 0).sum())
# raw cross-check
m_nonsip = m[m["Investment Type"].astype(str).str.upper().str.replace(" ","")=="NONSIP"]
raw_nonsip_nonzero = int((pd.to_numeric(m_nonsip["Current Installment Amount"], errors="coerce").fillna(0) != 0).sum())
chk("L3", "Current Installment Amount == 0 for all Non-SIP",
    nonsip_nonzero == 0,
    f"clean Non-SIP rows={len(nonsip)}, nonzero installment={nonsip_nonzero}; "
    f"raw Non-SIP nonzero={raw_nonsip_nonzero}")

# 10. Age flags: count outside [18,100] documented; not silently dropped
age = pd.to_numeric(ac["age"], errors="coerce")
out_of_range = int(((age < 18) | (age > 100)).sum())
age_missing = int(age.isna().sum())
flag_oor = int(ac["flag_age_out_of_range"].sum())
flag_missing = int(ac["flag_age_missing"].sum())
chk("L4", "Age out-of-range flagged not dropped (rows conserved)",
    len(ac) == n_master and flag_oor == out_of_range and flag_missing == age_missing,
    f"clean rows={len(ac)} == master {n_master}; recomputed out_of_range={out_of_range} "
    f"vs flag={flag_oor}; recomputed missing={age_missing} vs flag={flag_missing}")

# 11. monthly_flows reconcile to transactions_clean by type
tx_tot = tx.groupby("transaction_type")["amount"].sum().to_dict()
mf_pur = mf["purchase_amount"].sum()
mf_sur = mf["surrender_amount"].sum()
mf_div = mf["dividend_amount"].sum()
def close(a,b,tol=0.01): return abs(a-b) <= tol
rec_pur = close(tx_tot.get("Purchase",0), mf_pur)
rec_sur = close(tx_tot.get("Surrender",0), mf_sur)
rec_div = close(tx_tot.get("Dividend",0), mf_div)
# magnitude sanity vs brief (~5.22bn / ~2.73bn / ~0.25bn)
mag = (4.5e9 < tx_tot.get("Purchase",0) < 6e9) and (2e9 < tx_tot.get("Surrender",0) < 3.5e9) \
      and (1e8 < tx_tot.get("Dividend",0) < 4e8)
chk("L5", "monthly_flows totals reconcile to transactions_clean by type",
    rec_pur and rec_sur and rec_div and mag,
    f"Purchase tx={tx_tot.get('Purchase'):,.2f} mf={mf_pur:,.2f} | "
    f"Surrender tx={tx_tot.get('Surrender'):,.2f} mf={mf_sur:,.2f} | "
    f"Dividend tx={tx_tot.get('Dividend'):,.2f} mf={mf_div:,.2f}")
# Also reconcile transactions_clean back to raw (minus orphans)
led_no_orph = led[~led["Account Number"].astype(str).isin(orphan_accts)]
raw_tot = led_no_orph.groupby("Type of Transaction")["Total"].sum().to_dict()
rec_raw = close(raw_tot.get("Purchase",0), tx_tot.get("Purchase",0)) and \
          close(raw_tot.get("Surrender",0), tx_tot.get("Surrender",0)) and \
          close(raw_tot.get("Dividend",0), tx_tot.get("Dividend",0))
chk("L5b", "transactions_clean totals == raw ledger (orphans removed)",
    rec_raw,
    f"raw(no orphan): Purchase={raw_tot.get('Purchase'):,.2f} Surrender={raw_tot.get('Surrender'):,.2f} "
    f"Dividend={raw_tot.get('Dividend'):,.2f}")

# ===== CHURN FLAGS =====
# strict members = {closed, discontinued}; broad adds inactive; suspended excluded from denominators
strict_recompute = ac["status"].isin(["closed","discontinued"])
broad_recompute = ac["status"].isin(["closed","discontinued","inactive"])
flag_strict_match = bool((ac["churn_strict"].astype(bool) == strict_recompute).all())
flag_broad_match = bool((ac["churn_broad"].astype(bool) == broad_recompute).all())
strict_count = int(ac["churn_strict"].sum())
broad_count = int(ac["churn_broad"].sum())
chk("C1", "churn_strict column == {closed,discontinued} exactly; count==4,178",
    flag_strict_match and strict_count == 4178,
    f"flag matches status definition={flag_strict_match}; count={strict_count} (expected 4178)")
chk("C2", "churn_broad column == {closed,discontinued,inactive} exactly; count==5,302",
    flag_broad_match and broad_count == 5302,
    f"flag matches status definition={flag_broad_match}; count={broad_count} (expected 5302)")
# suspended excluded from rate denominators
excl = ac["excluded_from_rates"].astype(bool)
susp = ac["status"] == "suspended"
excl_match = bool((excl == susp).all())
chk("C3", "excluded_from_rates == suspended exactly (2 rows)",
    excl_match and int(susp.sum()) == 2,
    f"excluded_from_rates sum={int(excl.sum())}, suspended sum={int(susp.sum())}, match={excl_match}")
# churn flags must NOT include suspended
strict_has_susp = int((ac["churn_strict"].astype(bool) & susp).sum())
broad_has_susp = int((ac["churn_broad"].astype(bool) & susp).sum())
chk("C4", "Suspended not counted in churn_strict or churn_broad",
    strict_has_susp == 0 and broad_has_susp == 0,
    f"suspended in strict={strict_has_susp}, in broad={broad_has_susp}")

# ---------------- OUTPUT ----------------
print("="*70)
n_fail = sum(1 for r in results if r[2]=="FAIL")
for cid, desc, st, ev in results:
    print(f"[{st}] {cid} {desc}")
    print(f"        evidence: {ev}")
print("="*70)
print(f"TOTAL: {len(results)} checks, {n_fail} FAIL")
print("GATE 1:", "PASS" if n_fail==0 else "FAIL")

# dump machine-readable for report authoring
with open(f"{ROOT}/qa/_gate1_results.json","w") as f:
    json.dump([{"id":c,"desc":d,"status":s,"evidence":e} for c,d,s,e in results], f, indent=2)
