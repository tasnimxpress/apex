"""Builder for analysis/synthesis.ipynb -- cross-cut fund x segment x RM."""
from pathlib import Path
from _nbgen import md, code, build

SEC = "synthesis"
cells = []

cells.append(md(
"# Synthesis — Fund × Segment × RM\n"
"**Apex Asset Management case study · Agent 2 (Analysis) · as-of 2026-05-31**\n\n"
"This notebook cross-cuts the three sections into one picture of where AUM is made and lost, then "
"converts every finding into a **specific, owner-assigned recommendation tied to a number**. It "
"consumes the metric tables emitted by `section1/2/3` (no recomputation of raw business rules).\n\n"
"> **Caveat carried forward:** \"performance\" throughout = flow / retention / engagement, **not** "
"investment return — there is no NAV series in the data."
))

cells.append(code(
"import sys; sys.path.insert(0,'.')\n"
"import json, numpy as np, pandas as pd\n"
"import matplotlib.pyplot as plt\n"
"import _common as C\n"
"defs=C.load_defs(); C.set_style(); SEC='synthesis'\n"
"FUNDS=defs['funds']; SHORT=C.FUND_SHORT; COL=C.FUND_COLORS\n"
"A=C.ANALYSIS\n"
"m1=json.load(open(A/'section1/_metrics.json'))\n"
"m2=json.load(open(A/'section2/_metrics.json'))\n"
"m3=json.load(open(A/'section3/_metrics.json'))\n"
"acc=C.load_accounts()\n"
"seg=pd.read_csv(A/'section2/tables/customer_segments.csv')\n"
"seg['mobile_no']=seg['mobile_no'].astype(str); acc['mobile_no']=acc['mobile_no'].astype(str)\n"
"print('loaded section metrics + segment table', seg.shape)"
))

# ---- fund x segment ----
cells.append(md(
"## A. Fund × Segment — who holds what, and where the cross-sell sits\n"
"Map customer segments (Section 2) onto their dominant fund. This tells the fund manager which "
"customer type defends each fund and which segment to target for growth."
))
cells.append(code(
"fs=pd.crosstab(seg.dominant_fund, seg.segment)\n"
"fs=fs.reindex(FUNDS)\n"
"C.save_table(fs,SEC,'fund_x_segment_counts')\n"
"fig,ax=plt.subplots(figsize=(10,4.6))\n"
"im=ax.imshow(fs.values, cmap='Blues', aspect='auto')\n"
"ax.set_xticks(range(len(fs.columns))); ax.set_xticklabels(fs.columns, rotation=20, ha='right')\n"
"ax.set_yticks(range(len(fs.index))); ax.set_yticklabels([SHORT[f] for f in fs.index])\n"
"for i in range(fs.shape[0]):\n"
"    for j in range(fs.shape[1]):\n"
"        ax.text(j,i,int(fs.values[i,j]),ha='center',va='center',\n"
"                color='white' if fs.values[i,j]>fs.values.max()/2 else 'black', fontsize=9)\n"
"ax.set_title('Customers by dominant fund × segment'); plt.colorbar(im,label='customers')\n"
"C.savefig(fig,SEC,'01_fund_x_segment'); plt.show()\n"
"fs"
))

# ---- fund x RM ----
cells.append(md(
"## B. Fund × RM — align acquisition firepower to the funds that need it\n"
"Which RMs introduce each fund's book, overlaid with the fund's leakage (Section 1) and the RM's "
"retention (Section 3). The play: point **high-retention** RMs at the **highest-leakage** funds."
))
cells.append(code(
"intro=acc[acc.introducer_in_rmlist]\n"
"fr=pd.crosstab(intro.introducer_rm_name_canon, intro.fund).reindex(columns=FUNDS).fillna(0).astype(int)\n"
"C.save_table(fr,SEC,'fund_x_rm_counts')\n"
"# fund leakage (strict churn) from section1 scorecard\n"
"sc1=pd.DataFrame(m1['fund_scorecard']).set_index('fund')\n"
"rank=pd.DataFrame(m1['fund_ranking']).set_index('fund')\n"
"ret3=pd.DataFrame(m3['rm_retention_1yr']).set_index('introducer_rm_name_canon')\n"
"print('Fund leakage (strict churn %) and composite rank:')\n"
"print((sc1[['churn_strict']].assign(churn_pct=lambda d:(d.churn_strict*100).round(1))\n"
"       .join(rank[['composite_score','rank']]))[['churn_pct','composite_score','rank']])\n"
"# top introducing RM per fund\n"
"top_rm_fund={f: fr[f].idxmax() for f in FUNDS}\n"
"print('\\nTop introducing RM per fund:')\n"
"for f in FUNDS: print(f'  {SHORT[f]:16}: {top_rm_fund[f]} ({fr.loc[top_rm_fund[f],f]} accts)')"
))

# ---- segment x RM ----
cells.append(md(
"## C. Segment × RM — who acquires high-value customers\n"
"Cross-cut the acquired segment mix per RM. RMs who disproportionately bring in the high-value "
"segment are the template; those bringing only small-ticket starters need a value-mix nudge."
))
cells.append(code(
"acc_seg=acc.merge(seg[['mobile_no','segment']].drop_duplicates('mobile_no'), on='mobile_no', how='left')\n"
"intro_seg=acc_seg[acc_seg.introducer_in_rmlist]\n"
"sr=pd.crosstab(intro_seg.introducer_rm_name_canon, intro_seg.segment, normalize='index')*100\n"
"C.save_table(sr,SEC,'segment_x_rm_pct')\n"
"hv_col=[c for c in sr.columns if 'High-value' in c]\n"
"if hv_col:\n"
"    hv=sr[hv_col[0]].sort_values(ascending=False)\n"
"    print('Share of each RM\\'s book that is the High-value segment (%):')\n"
"    print(hv.round(1).to_string())\n"
"sr.round(1)"
))

# ---- consolidated recommendations ----
cells.append(md(
"## D. Consolidated recommendation register\n"
"Every finding → a single accountable **owner**, a concrete **action**, and the **number** it is "
"tied to. This is the Monday-morning to-do list."
))
cells.append(code(
"# pull the numbers we cite so the register is reproducible\n"
"worst_fund=rank.sort_values('composite_score').index[0]\n"
"best_fund=rank.sort_values('composite_score').index[-1]\n"
"leakiest=sc1.churn_strict.idxmax()\n"
"xs=pd.DataFrame(m2['cross_sell'])\n"
"p1=xs.iloc[0]; p3=xs.iloc[2]\n"
"flag_rms=m3['high_vol_low_quality_rms']\n"
"surr=m1['surrender_timing']\n"
"pers=m1['sip_persistency_overall']\n"
"recs=[\n"
" dict(area='Fund', owner='Head of Funds / PM — '+SHORT[worst_fund],\n"
"   finding=f'{SHORT[worst_fund]} ranks last on durable-growth composite ({rank.loc[worst_fund,\"composite_score\"]:.0f}/100)',\n"
"   action='Diagnose leakage + redesign retention proposition before chasing new flows', number=f'composite {rank.loc[worst_fund,\"composite_score\"]:.0f}'),\n"
" dict(area='Fund', owner='Head of Funds / PM — '+SHORT[leakiest],\n"
"   finding=f'Highest strict-churn fund = {SHORT[leakiest]} ({sc1.loc[leakiest,\"churn_strict\"]*100:.1f}%)',\n"
"   action='Targeted win-back on closed/discontinued accounts in this fund', number=f'{sc1.loc[leakiest,\"churn_strict\"]*100:.1f}% churn'),\n"
" dict(area='SIP', owner='Head of Retention / Ops',\n"
"   finding=f'Overall SIP persistency {pers*100:.1f}% of expected installments paid; decay accelerates after the early months',\n"
"   action='Trigger a save-the-SIP call at the first missed installment (auto-flag from monthly_flows)', number=f'{pers*100:.1f}% persistency'),\n"
" dict(area='Fund', owner='Marketing + PM',\n"
"   finding=f'Surrenders run {surr[\"surrender_share_month_after\"]*100:.0f}% in the month AFTER dividends vs {surr[\"uniform_baseline\"]*100:.0f}% uniform',\n"
"   action='Pre-empt with a reinvest-your-dividend offer issued WITH each distribution', number=f'{surr[\"surrender_share_month_after\"]*100:.0f}% post-dividend surrenders'),\n"
" dict(area='Cross-sell', owner='Head of Sales',\n"
"   finding=f'{int(p1.target_customers)} active single-fund customers; multi-fund penetration low',\n"
"   action='Second-fund campaign to single-fund holders via their existing servicing RM', number=C.taka(p1.taka)),\n"
" dict(area='Cross-sell', owner='Head of Sales',\n"
"   finding=f'{int(p3.target_customers)} lump-sum-only (Non-SIP) customers carry no recurring stream',\n"
"   action='Non-SIP → SIP migration offer to convert one-off money into a persistency asset', number=C.taka(p3.taka)+'/yr'),\n"
" dict(area='RM', owner='Sales Manager (1:1 coaching)',\n"
"   finding=f'High-volume / low-retention RMs: {\", \".join(flag_rms) if flag_rms else \"none flagged\"}',\n"
"   action='Coach on acquisition quality; tie a slice of incentive to 1-yr retention, not just sign-ups', number=f'{len(flag_rms)} RMs flagged'),\n"
" dict(area='RM', owner='Head of Sales (allocation)',\n"
"   finding='Specialist (high-HHI) RMs are concentrated in single funds',\n"
"   action=f'Deploy high-retention specialists onto {SHORT[leakiest]} (highest-leakage fund)', number='HHI map in section3'),\n"
"]\n"
"reg=pd.DataFrame(recs)[['area','owner','finding','action','number']]\n"
"C.save_table(reg,SEC,'recommendation_register',index=False)\n"
"json.dump({'worst_fund':worst_fund,'best_fund':best_fund,'leakiest_fund':leakiest,\n"
"           'flag_rms':flag_rms}, open(A/SEC/'_metrics.json','w'), indent=2)\n"
"pd.set_option('display.max_colwidth',60)\n"
"reg"
))
cells.append(code(
"# one consolidated 'where AUM is made vs lost' chart for the deck\n"
"fig,ax=plt.subplots(figsize=(10,5))\n"
"order=rank.sort_values('composite_score',ascending=False).index\n"
"x=np.arange(len(order)); w=0.6\n"
"nf=[sc1.loc[f,'net_flow_value']/1e7 for f in order]\n"
"ax.bar(x, nf, w, color=[COL[f] for f in order])\n"
"for xi,f in zip(x,order):\n"
"    ax.text(xi, nf[list(order).index(f)]+1, f\"churn {sc1.loc[f,'churn_strict']*100:.0f}%\", ha='center', fontsize=9)\n"
"ax.set_xticks(x); ax.set_xticklabels([f'{SHORT[f]}\\n#{int(rank.loc[f,\"rank\"])}' for f in order])\n"
"ax.set_ylabel('Lifetime net flow ৳Cr'); ax.set_title('Where AUM is made vs lost — net flow by fund (rank, churn labelled)')\n"
"C.savefig(fig,SEC,'02_aum_made_vs_lost'); plt.show()\n"
"print('figures:', sorted(p.name for p in (A/SEC/'figures').glob('*.png')))\n"
"print('tables :', sorted(p.name for p in (A/SEC/'tables').glob('*.csv')))"
))

cells.append(md(
"## Synthesis headline\n"
"**Apex's growth problem is a retention problem, not an acquisition problem.** Net flow is strongly "
"positive and growing, but it is concentrated in one fund (Fixed Income) while the others leak; the "
"base is overwhelmingly single-fund; and a couple of high-volume RMs acquire faster than they "
"retain. The three highest-leverage moves — all owner-assigned above — are: (1) defend the leakiest "
"fund and fix SIP persistency at the first missed installment, (2) run a second-fund campaign to "
"existing single-fund customers (cheapest AUM available), and (3) re-tie RM incentives to 1-year "
"retention. See `recommendation_register.csv` for the full owner-assigned list."
))

build(cells, Path("synthesis.ipynb"))
print("built synthesis.ipynb")
