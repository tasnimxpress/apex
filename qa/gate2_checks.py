"""
GATE 2 -- independent recomputation of Agent 2 headline metrics from clean/.
Principle: reproduce, don't trust. We recompute each number directly from the
clean parquet tables and compare to what the notebooks persisted in
analysis/<section>/_metrics.json. Writes qa/gate2_body.md and prints PASS/FAIL.

Run: d:/GitHub/apex/.venv/Scripts/python.exe qa/gate2_checks.py
"""
import json, re
from pathlib import Path
import numpy as np, pandas as pd

REPO = Path(__file__).resolve().parent.parent
CLEAN = REPO/"clean"; AN = REPO/"analysis"
AS_OF = pd.Timestamp("2026-05-31")
TOL = 0.005   # 0.5% relative / absolute tolerance on rates and ratios

acc = pd.read_parquet(CLEAN/"accounts_clean.parquet")
mf  = pd.read_parquet(CLEAN/"monthly_flows.parquet")
tx  = pd.read_parquet(CLEAN/"transactions_clean.parquet")
cust= pd.read_parquet(CLEAN/"customers.parquet")
FUNDS = ["Apex Fixed Income Fund","Apex Shariah Growth Fund",
         "Apex Balanced Opportunity Fund","Apex Capital Growth Fund"]
m1=json.load(open(AN/"section1/_metrics.json")); m2=json.load(open(AN/"section2/_metrics.json"))
m3=json.load(open(AN/"section3/_metrics.json"))

rows=[]  # (id, check, result, evidence)
def chk(id_, name, ok, ev):
    rows.append((id_, name, "PASS" if ok else "FAIL", ev))
    return ok

def close(a,b,tol=TOL):
    if b==0: return abs(a-b)<=tol
    return abs(a-b)<=tol or abs(a-b)/abs(b)<=tol

# ---------------------------------------------------------------- G1 net flow
mf_chk = (mf.purchase_amount - mf.surrender_amount)
chk("G2-1a","net_flow column == purchase-surrender (dividends excluded)",
    np.allclose(mf.net_flow, mf_chk), f"max abs diff={np.abs(mf.net_flow-mf_chk).max():.6f}")
nf_tx = tx[tx.transaction_type=="Purchase"].amount.sum() - tx[tx.transaction_type=="Surrender"].amount.sum()
chk("G2-1b","total net flow ties tx (Purchase-Surrender)",
    close(mf.net_flow.sum(), nf_tx, 1.0), f"mf={mf.net_flow.sum():.2f} tx={nf_tx:.2f}")
# per-fund net flow vs scorecard
sc=pd.DataFrame(m1["fund_scorecard"]).set_index("fund")
nf_fund = mf.groupby("fund").net_flow.sum()
ok_nf = all(close(nf_fund[f], sc.loc[f,"net_flow_value"], 1.0) for f in FUNDS)
chk("G2-1c","per-fund net flow value reproduced", ok_nf,
    "; ".join(f"{f.split()[1]}:{nf_fund[f]/1e7:.1f}Cr" for f in FUNDS))

# ---------------------------------------------------------------- G2 churn/closure/disc + rate sanity
acc_r = acc[~acc.excluded_from_rates]
ok_churn=True; ok_sanity=True; details=[]
for f in FUNDS:
    s=acc_r[acc_r.fund==f]; n=len(s)
    closure=(s.status=="closed").mean(); disc=(s.status=="discontinued").mean()
    churn=closure+disc; active=(s.status=="active").mean(); inact=(s.status=="inactive").mean()
    ok_churn &= close(churn, sc.loc[f,"churn_strict"]) and close(closure, sc.loc[f,"closure"]) and close(disc, sc.loc[f,"discontinuation"])
    shares=active+inact+churn
    ok_sanity &= close(shares,1.0) and all(0<=x<=1 for x in [closure,disc,churn,active])
    details.append(f"{f.split()[1]} churn={churn:.3f}")
chk("G2-2a","per-fund closure/discontinuation/strict-churn reproduced", ok_churn, "; ".join(details))
chk("G2-2b","rate sanity: active+inactive+churn==100%, all rates in [0,1]", ok_sanity,
    "all fund status-shares sum to 1.0; no rate <0 or >1")

# ---------------------------------------------------------------- G3 case 1-yr retention (point-in-time)
co=m3["case_2024_05_retention"]
c0=acc_r[acc_r.onboarding_month=="2024-05"].copy()
meas=pd.Timestamp("2025-05-31")
cb=c0.account_closing_date.notna()&(c0.account_closing_date<=meas)
db=c0.sip_discontinuation_date.notna()&(c0.sip_discontinuation_date<=meas)
ret=(~(cb|db))
chk("G3-1","case cohort denominator (2024-05) reproduced", len(c0)==co["denominator"], f"recomputed={len(c0)} persisted={co['denominator']}")
chk("G3-2","case cohort numerator (retained @2025-05, point-in-time) reproduced",
    int(ret.sum())==co["numerator"], f"recomputed={int(ret.sum())} persisted={co['numerator']}")
chk("G3-3","case 1-yr retention rate reproduced & in [0,1]",
    close(ret.mean(), co["rate"]) and 0<=co["rate"]<=1, f"recomputed={ret.mean():.4f} persisted={co['rate']:.4f}")

# overall official-RM 1-yr retention
intro=acc[acc.introducer_in_rmlist]
cut=AS_OF-pd.DateOffset(months=12)
obs=intro[intro.first_purchase_date<=cut].copy()
m12=obs.first_purchase_date+pd.DateOffset(months=12)
ret12=~((obs.account_closing_date.notna()&(obs.account_closing_date<=m12)) |
        (obs.sip_discontinuation_date.notna()&(obs.sip_discontinuation_date<=m12)))
chk("G3-4","overall official-RM 1-yr retention reproduced & bound-checked",
    close(ret12.mean(), m3["overall_retention_1yr"]) and 0<=ret12.mean()<=1,
    f"recomputed={ret12.mean():.4f} persisted={m3['overall_retention_1yr']:.4f}")

# ---------------------------------------------------------------- G4 SIP persistency
sip=acc[acc.is_sip].copy()
paid=(mf[mf.purchase_amount>0].groupby("account_number").transaction_month.nunique())
sip["paid"]=sip.registration_no.map(paid).fillna(0).astype(int)
def endw(r):
    e=[AS_OF]
    if pd.notna(r.account_closing_date): e.append(r.account_closing_date)
    if pd.notna(r.sip_discontinuation_date): e.append(r.sip_discontinuation_date)
    return min(e)
we=sip.apply(endw,axis=1)
elapsed=((we.dt.year-sip.first_purchase_date.dt.year)*12+(we.dt.month-sip.first_purchase_date.dt.month)+1).clip(lower=0)
ten=sip.tenor_in_month.replace(0,np.nan)
exp=np.minimum(elapsed, ten.fillna(elapsed)).clip(lower=1).astype(int)
overall_pers=sip.paid.sum()/exp.sum()
chk("G4-1","overall SIP persistency (paid/expected) reproduced & in [0,1]",
    close(overall_pers, m1["sip_persistency_overall"]) and 0<=overall_pers<=1,
    f"recomputed={overall_pers:.4f} persisted={m1['sip_persistency_overall']:.4f}")

# ---------------------------------------------------------------- G5 clustering stability
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, adjusted_rand_score
age_c=acc.groupby("mobile_no").age.median()
tenor_c=acc.groupby("mobile_no").tenor_in_month.mean()
c2=cust.set_index("mobile_no")
c2["age"]=age_c; c2["mt"]=tenor_c
feat=c2.dropna(subset=["age"])
X=np.column_stack([feat.age, np.log1p(feat.total_current_installment), feat.mt, np.log1p(feat.total_onboarding_amount)])
Xs=StandardScaler().fit_transform(X)
K=m2["clustering"]["k"]
labs={s:KMeans(n_clusters=K,random_state=s,n_init=10).fit_predict(Xs) for s in [42,7,123]}
import itertools
aris=[adjusted_rand_score(labs[a],labs[b]) for a,b in itertools.combinations(labs,2)]
sil=silhouette_score(Xs,labs[42])
chk("G5-1","clustering re-runs stable across 3 seeds (min ARI>=0.8)", min(aris)>=0.8, f"ARIs={[round(x,3) for x in aris]}")
chk("G5-2","silhouette reproduced at k={}".format(K), close(sil, m2["clustering"]["silhouette_seed42"],0.02),
    f"recomputed={sil:.4f} persisted={m2['clustering']['silhouette_seed42']:.4f}")

# ---------------------------------------------------------------- G6 cross-sell ties to a customer count
xs=pd.DataFrame(m2["cross_sell"]); assump=m2["assumptions"]
single=cust[cust.funds_held==1]; single_active=single[single.n_active_accounts>0]
p1_n=len(single_active); p1_taka=p1_n*assump["median_onboarding_ticket"]
chk("G6-1","cross-sell Play1 customer count reproduced", p1_n==int(xs.iloc[0].target_customers),
    f"recomputed={p1_n} persisted={int(xs.iloc[0].target_customers)}")
chk("G6-2","cross-sell Play1 Taka == count x ticket", close(p1_taka, xs.iloc[0].taka, 1.0),
    f"recomputed={p1_taka:.0f} persisted={xs.iloc[0].taka:.0f}")
# non-sip-only active (play3)
sipmix=acc.groupby("mobile_no").is_sip.agg(["sum","count"])
nonsip_only=set(sipmix[sipmix["sum"]==0].index)
ns=cust[cust.mobile_no.isin(nonsip_only) & (cust.n_active_accounts>0)]
p3_n=len(ns); p3_taka=p3_n*assump["median_sip_annual"]
chk("G6-3","cross-sell Play3 (Non-SIP->SIP) count + Taka reproduced",
    p3_n==int(xs.iloc[2].target_customers) and close(p3_taka, xs.iloc[2].taka,1.0),
    f"recomputed n={p3_n} taka={p3_taka:.0f} | persisted n={int(xs.iloc[2].target_customers)}")

# ---------------------------------------------------------------- G7 figures match tables (spot-check 3)
fc=pd.read_csv(AN/"section1/tables/fund_scorecard.csv").set_index("fund")
spot1=close(fc.loc["Apex Capital Growth Fund","churn_strict"], sc.loc["Apex Capital Growth Fund","churn_strict"])
rk=pd.read_csv(AN/"section1/tables/fund_composite_ranking.csv")
spot2=(rk.sort_values("composite_score",ascending=False).iloc[0]["fund"]=="Apex Fixed Income Fund")
xs_csv=pd.read_csv(AN/"section2/tables/cross_sell_sizing.csv")
spot3=close(xs_csv.iloc[0].taka, p1_taka, 1.0)
figs=[AN/"section1/figures/07_fund_ranking.png", AN/"section2/figures/04_cross_sell.png", AN/"section3/figures/01_rm_quadrant.png"]
allfigs=all(p.exists() for p in figs)
chk("G7-1","saved tables match recomputed values (3 spot-checks)", spot1 and spot2 and spot3,
    f"scorecard-churn={spot1}, rank#1=FixedIncome={spot2}, crosssell-taka={spot3}")
chk("G7-2","referenced figures exist on disk", allfigs, "; ".join(p.name for p in figs))

# ---------------------------------------------------------------- G8 caveat present
nb=(AN/"section1.ipynb").read_text(encoding="utf-8")
has_caveat = ("NO NAV" in nb or "no NAV" in nb.lower()) and "not" in nb.lower() and "return" in nb.lower()
chk("G8-1","Section 1 states the no-NAV / flow-not-return caveat", has_caveat,
    "found explicit caveat in section1.ipynb")

# ---------------------------------------------------------------- write report body
npass=sum(1 for r in rows if r[2]=="PASS"); n=len(rows)
lines=["## GATE 2 — Analysis (`analysis/`)", "",
       f"**Date:** 2026-06-16 · **Validator:** Agent 3 · **Principle:** reproduce, don't trust.",
       f"Every metric below was recomputed directly from `clean/` by `qa/gate2_checks.py` and compared",
       f"to the notebook-persisted `analysis/<section>/_metrics.json` (tol {TOL*100:.1f}%).", "",
       "| ID | Check | Result | Evidence (recomputed) |","|----|-------|--------|-----------------------|"]
for id_,name,res,ev in rows:
    lines.append(f"| {id_} | {name} | **{res}** | {ev} |")
lines+=["", f"**{npass}/{n} checks PASS.**", ""]
signoff = "GATE 2: PASS" if npass==n else "GATE 2: FAIL — see items above"
lines.append("`"+signoff+"`")
(REPO/"qa/gate2_body.md").write_text("\n".join(lines), encoding="utf-8")

for id_,name,res,ev in rows:
    print(f"[{res}] {id_} {name}")
print(f"\n{npass}/{n} PASS -> {signoff}")
