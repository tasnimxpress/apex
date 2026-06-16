"""Builder for analysis/section3.ipynb -- RM Productivity."""
from pathlib import Path
from _nbgen import md, code, build

SEC = "section3"
cells = []

cells.append(md(
"# Section 3 — RM Productivity\n"
"**Apex Asset Management case study · Agent 2 (Analysis) · as-of 2026-05-31**\n\n"
"Acquisition metrics are attributed on the **Introducer** role (who onboarded the account) per "
"`definitions.rm` — never blended with the servicing book. We score the 16 official RMs on "
"volume **and** quality (1-year cohort retention), map the volume×value quadrant, measure fund "
"specialisation via **HHI**, and read the team's year-over-year trajectory to separate **systemic** "
"from **individual** problems."
))

cells.append(code(
"import sys; sys.path.insert(0,'.')\n"
"import numpy as np, pandas as pd\n"
"import matplotlib.pyplot as plt\n"
"import _common as C\n"
"defs=C.load_defs(); C.set_style(); SEC='section3'; AS_OF=C.AS_OF\n"
"acc=C.load_accounts(); mf=C.load_monthly_flows()\n"
"FUNDS=defs['funds']; SHORT=C.FUND_SHORT; COL=C.FUND_COLORS; metrics={}\n"
"# Official-RM introduced book (acquisition role)\n"
"intro=acc[acc.introducer_in_rmlist].copy()\n"
"print('accounts introduced by the 16 official RMs:', len(intro), 'of', len(acc))\n"
"print('distinct official introducer RMs:', intro.introducer_rm_name_canon.nunique())"
))

# ---- 3.1 RM scorecard ----
cells.append(md(
"## 3.1 RM scorecard (acquisition role = Introducer)\n"
"Per RM: unique customers onboarded, accounts introduced, average installment, **AUM introduced** "
"(current book value of accounts they onboarded), onboarding capital, and headline leakage of "
"their book."
))
cells.append(code(
"def rm_card(df):\n"
"    g=df.groupby('introducer_rm_name_canon')\n"
"    sc=g.agg(accounts=('registration_no','size'),\n"
"             customers=('mobile_no','nunique'),\n"
"             avg_installment=('current_installment_amount','mean'),\n"
"             aum_introduced=('investment_value_market','sum'),\n"
"             onboarding_capital=('onboarding_amount','sum'),\n"
"             sip_share=('is_sip','mean'))\n"
"    rate=df[~df.excluded_from_rates]\n"
"    rr=rate.groupby('introducer_rm_name_canon').agg(\n"
"        churn_strict=('churn_strict','mean'),\n"
"        active_now=('is_active','mean'))\n"
"    return sc.join(rr)\n"
"card=rm_card(intro).sort_values('aum_introduced',ascending=False)\n"
"C.save_table(card,SEC,'rm_scorecard')\n"
"metrics['rm_scorecard']=card.reset_index().to_dict('records')\n"
"disp=card.copy()\n"
"disp['avg_installment']=disp.avg_installment.round(0)\n"
"disp['aum_introduced_Cr']=(disp.aum_introduced/1e7).round(2)\n"
"disp['onboarding_Cr']=(disp.onboarding_capital/1e7).round(2)\n"
"for c in ['sip_share','churn_strict','active_now']: disp[c]=(disp[c]*100).round(1)\n"
"disp[['accounts','customers','avg_installment','aum_introduced_Cr','onboarding_Cr','sip_share','churn_strict','active_now']]"
))

# ---- 3.2 per-RM 1-yr retention ----
cells.append(md(
"## 3.2 Per-RM 1-year cohort retention — *acquisition quality*\n"
"Volume without retention is churned AUM. For every account we reconstruct its **point-in-time "
"status at onboarding + 12 months** (using dated close/discontinue events, not the current "
"snapshot — see `decisions_log.md`), restricted to accounts old enough to observe that outcome "
"(onboarded ≤ as-of − 12m). Per-RM 1-yr retention = share of their introduced cohort still alive "
"(not strict-churned) at month 12. **High volume + low retention = the flag to coach.**"
))
cells.append(code(
"# observable 12-month cohort: onboarded on/before AS_OF - 12 months\n"
"cut = AS_OF - pd.DateOffset(months=12)\n"
"obs = intro[intro.first_purchase_date<=cut].copy()\n"
"measure = obs.first_purchase_date + pd.DateOffset(months=12)\n"
"closed_by = obs.account_closing_date.notna() & (obs.account_closing_date<=measure)\n"
"disc_by   = obs.sip_discontinuation_date.notna() & (obs.sip_discontinuation_date<=measure)\n"
"obs['retained_12m'] = ~(closed_by|disc_by)\n"
"ret=obs.groupby('introducer_rm_name_canon').agg(\n"
"    cohort_n=('retained_12m','size'), retention_1yr=('retained_12m','mean'))\n"
"card=card.join(ret)\n"
"metrics['rm_retention_1yr']=ret.reset_index().to_dict('records')\n"
"metrics['overall_retention_1yr']=float(obs.retained_12m.mean())\n"
"print(f'Overall 1-yr cohort retention (official-RM book): {obs.retained_12m.mean():.1%}  (n={len(obs)})')\n"
"C.save_table(card,SEC,'rm_scorecard_with_retention')\n"
"(ret.assign(retention_1yr=(ret.retention_1yr*100).round(1)).sort_values('retention_1yr'))"
))
cells.append(code(
"# Case-specified 1-yr retention (May-2024 cohort -> May-2025), reconstructed point-in-time\n"
"co=defs['cohorts']['one_year_retention']\n"
"acc_all=acc[~acc.excluded_from_rates]\n"
"c0=acc_all[acc_all.onboarding_month==co['cohort_month']].copy()\n"
"meas=pd.Timestamp(co['measured_at']+'-28') + pd.offsets.MonthEnd(0)\n"
"cb=c0.account_closing_date.notna()&(c0.account_closing_date<=meas)\n"
"db=c0.sip_discontinuation_date.notna()&(c0.sip_discontinuation_date<=meas)\n"
"c0['retained']=~(cb|db)\n"
"metrics['case_2024_05_retention']=dict(cohort_month=co['cohort_month'],measured_at=co['measured_at'],\n"
"    denominator=int(len(c0)), numerator=int(c0.retained.sum()), rate=float(c0.retained.mean()))\n"
"print(f\"Case cohort {co['cohort_month']} -> {co['measured_at']}: \"\n"
"      f\"{int(c0.retained.sum())}/{len(c0)} retained = {c0.retained.mean():.1%}\")"
))

# ---- 3.3 volume x value quadrant ----
cells.append(md(
"## 3.3 Volume × value quadrant + retention overlay\n"
"x = customers onboarded (volume), y = AUM introduced per customer (value). Split at medians. "
"Bubble size = cohort size; colour = 1-yr retention. The dangerous quadrant is **high-volume, "
"low-value/low-retention** — RMs spraying low-quality sign-ups."
))
cells.append(code(
"q=card.dropna(subset=['retention_1yr']).copy()\n"
"q['aum_per_customer']=q.aum_introduced/q.customers\n"
"vmed=q.customers.median(); amed=q.aum_per_customer.median()\n"
"metrics['quadrant_medians']=dict(volume_median=float(vmed), value_median=float(amed))\n"
"fig,ax=plt.subplots(figsize=(10,6.5))\n"
"sc=ax.scatter(q.customers, q.aum_per_customer/1e5, s=q.cohort_n/2+30,\n"
"    c=q.retention_1yr*100, cmap='RdYlGn', vmin=50, vmax=100, edgecolor='k', linewidth=.6)\n"
"ax.axvline(vmed,ls='--',color='grey'); ax.axhline(amed/1e5,ls='--',color='grey')\n"
"for n,r in q.iterrows(): ax.annotate(str(n)[:14], (r.customers, r.aum_per_customer/1e5), fontsize=7,\n"
"    xytext=(3,3), textcoords='offset points')\n"
"ax.set_xlabel('Customers onboarded (volume)'); ax.set_ylabel('AUM introduced per customer (৳ Lakh, value)')\n"
"ax.set_title('RM volume × value quadrant (colour = 1-yr retention %)')\n"
"plt.colorbar(sc,label='1-yr retention %')\n"
"C.savefig(fig,SEC,'01_rm_quadrant'); plt.show()\n"
"# explicit high-volume/low-quality flag\n"
"flag=q[(q.customers>=vmed)&(q.retention_1yr<q.retention_1yr.median())]\n"
"metrics['high_vol_low_quality_rms']=flag.index.tolist()\n"
"print('High-volume / low-retention RMs to coach:', flag.index.tolist())"
))

# ---- 3.4 HHI specialization ----
cells.append(md(
"## 3.4 Fund specialisation via HHI\n"
"For each RM, HHI of their introduced accounts across the 4 funds (Σ shareᵢ², ×10,000). "
"~10,000 = one-fund specialist; ~2,500 = perfectly diversified. Specialists are efficient to "
"deploy on their fund but a single-fund concentration risk; generalists are flexible."
))
cells.append(code(
"def hhi(s):\n"
"    p=s.value_counts(normalize=True); return float((p**2).sum()*10000)\n"
"hh=intro.groupby('introducer_rm_name_canon').fund.apply(hhi).rename('HHI')\n"
"top_fund=intro.groupby('introducer_rm_name_canon').fund.agg(lambda s:s.value_counts().idxmax())\n"
"spec=pd.DataFrame({'HHI':hh,'primary_fund':top_fund,'accounts':intro.groupby('introducer_rm_name_canon').size()})\n"
"spec=spec.sort_values('HHI',ascending=False)\n"
"C.save_table(spec,SEC,'rm_specialization_hhi')\n"
"metrics['rm_hhi']=spec.reset_index().to_dict('records')\n"
"fig,ax=plt.subplots(figsize=(9,6))\n"
"order=spec.sort_values('HHI').index\n"
"cols=[COL[spec.loc[n,'primary_fund']] for n in order]\n"
"ax.barh([str(n)[:16] for n in order], spec.loc[order,'HHI'], color=cols)\n"
"ax.axvline(2500,ls='--',color='grey'); ax.text(2500,0,' even split',fontsize=8,color='grey')\n"
"ax.set_xlabel('HHI (fund concentration)'); ax.set_title('RM fund specialisation (colour = primary fund)')\n"
"C.savefig(fig,SEC,'02_rm_hhi'); plt.show()\n"
"spec.round(0)"
))

# ---- 3.5 team YoY ----
cells.append(md(
"## 3.5 Team year-over-year — systemic vs individual\n"
"Team trajectory by onboarding year: accounts introduced, 1-yr cohort retention of each vintage, "
"and net flow attributed to that vintage. A falling team-wide retention line is a **systemic** "
"signal (process/incentive); a single RM diverging is **individual** (coaching)."
))
cells.append(code(
"# vintage retention: reuse point-in-time +12m on the official-RM book by onboarding year\n"
"obs_y=intro[intro.first_purchase_date<=cut].copy()\n"
"m2=obs_y.first_purchase_date+pd.DateOffset(months=12)\n"
"obs_y['retained_12m']=~((obs_y.account_closing_date.notna()&(obs_y.account_closing_date<=m2)) |\n"
"                        (obs_y.sip_discontinuation_date.notna()&(obs_y.sip_discontinuation_date<=m2)))\n"
"team=obs_y.groupby('onboarding_year').agg(introduced=('registration_no','size'),\n"
"    retention_1yr=('retained_12m','mean'))\n"
"# net flow by introducing vintage\n"
"nf=mf.merge(intro[['registration_no','onboarding_year']],left_on='account_number',right_on='registration_no')\n"
"nf_y=nf.groupby('onboarding_year').net_flow.sum()\n"
"team['net_flow']=nf_y\n"
"C.save_table(team,SEC,'team_yoy')\n"
"metrics['team_yoy']=team.reset_index().to_dict('records')\n"
"fig,ax=plt.subplots(1,3,figsize=(15,4.3))\n"
"yy=team.index.astype(int)\n"
"ax[0].bar(yy,team.introduced,color='#2E5A87'); ax[0].set_title('Accounts introduced / vintage')\n"
"ax[1].plot(yy,team.retention_1yr*100,'o-',color='#9A3B5B'); ax[1].set_title('1-yr retention by vintage (%)'); ax[1].set_ylim(0,100)\n"
"ax[2].bar(yy,team.net_flow/1e7,color=['#3E8E7E' if v>=0 else '#9A3B5B' for v in team.net_flow]); ax[2].set_title('Net flow by vintage (৳Cr)')\n"
"fig.suptitle('Team trajectory by onboarding vintage', fontsize=14, fontweight='bold')\n"
"C.savefig(fig,SEC,'03_team_yoy'); plt.show()\n"
"team.assign(retention_1yr=(team.retention_1yr*100).round(1), net_flow_Cr=(team.net_flow/1e7).round(2)).drop(columns='net_flow')"
))
cells.append(code(
"C.dump_metrics(SEC,metrics)\n"
"print('Section 3 metrics persisted.')\n"
"print('figures:', sorted(p.name for p in (C.ANALYSIS/SEC/'figures').glob('*.png')))\n"
"print('tables :', sorted(p.name for p in (C.ANALYSIS/SEC/'tables').glob('*.csv')))"
))

cells.append(md(
"## 3.6 Section-3 findings (each a Monday decision)\n"
"- **Rank RMs on retention-adjusted volume, not raw sign-ups.** The volume×value quadrant flags "
"high-volume/low-retention RMs whose AUM leaks back out within a year — coach or re-incentivise them.\n"
"- **Specialists vs generalists are different tools:** high-HHI RMs are efficient to deploy on "
"their fund; pair them with the fund that needs growth (Section 1) rather than re-training them.\n"
"- **Read the vintage retention line for systemic drift:** if team-wide 1-yr retention is falling "
"across vintages, the fix is process/incentive (systemic), not individual coaching.\n"
"- Acquisition (Introducer) and book (Service) are kept separate so we don't credit a servicing RM "
"for another's onboarding."
))

build(cells, Path("section3.ipynb"))
print("built section3.ipynb")
