"""
analysis/_common.py  -- shared backbone for Agent 2 analysis notebooks.

Single source of truth = ../definitions.yaml (loaded, never overridden in code).
Consumes ONLY ../clean tables. If a clean table looks wrong, RAISE -- do not patch.

Every notebook starts with:
    import _common as C
    defs = C.load_defs()
    acc  = C.load_accounts()
    ...
"""
from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pandas as pd
import yaml

# ----------------------------------------------------------------------
# Paths (resolve repo root regardless of notebook cwd)
# ----------------------------------------------------------------------
REPO = Path(__file__).resolve().parent.parent
CLEAN = REPO / "clean"
ANALYSIS = REPO / "analysis"
DEFS_PATH = REPO / "definitions.yaml"

AS_OF = pd.Timestamp("2026-05-31")        # from definitions.project.as_of_date
RANDOM_SEED = 42

# ----------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------
def load_defs() -> dict:
    with open(DEFS_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# ----------------------------------------------------------------------
# Table loaders (parquet = contract-stable artifacts from Agent 1)
# ----------------------------------------------------------------------
def load_accounts() -> pd.DataFrame:
    return pd.read_parquet(CLEAN / "accounts_clean.parquet")

def load_customers() -> pd.DataFrame:
    return pd.read_parquet(CLEAN / "customers.parquet")

def load_transactions() -> pd.DataFrame:
    return pd.read_parquet(CLEAN / "transactions_clean.parquet")

def load_monthly_flows() -> pd.DataFrame:
    return pd.read_parquet(CLEAN / "monthly_flows.parquet")

def load_rm() -> pd.DataFrame:
    return pd.read_parquet(CLEAN / "rm_attribution.parquet")

# ----------------------------------------------------------------------
# Point-in-time status reconstruction  (cohorts, not snapshots)
# ----------------------------------------------------------------------
# `status` in accounts_clean is the CURRENT snapshot (as of AS_OF). For cohort
# retention measured at an earlier date we must reconstruct whether the account
# had churned *by that date* using the dated event columns. This is the rigorous
# cohort treatment the brief demands; logged in decisions_log.md.
def churned_strict_by(acc: pd.DataFrame, asof: pd.Timestamp) -> pd.Series:
    """True if account had CLOSED or DISCONTINUED on/before `asof` (strict churn)."""
    closed_by = acc["account_closing_date"].notna() & (acc["account_closing_date"] <= asof)
    disc_by = acc["sip_discontinuation_date"].notna() & (acc["sip_discontinuation_date"] <= asof)
    return closed_by | disc_by

def alive_strict_at(acc: pd.DataFrame, asof: pd.Timestamp) -> pd.Series:
    """Account exists (first purchase <= asof) and has NOT strict-churned by asof.
    Suspended (excluded_from_rates) is dropped by the caller via the denominator."""
    born = acc["first_purchase_date"].notna() & (acc["first_purchase_date"] <= asof)
    return born & ~churned_strict_by(acc, asof)

# ----------------------------------------------------------------------
# Rate helpers -- denominators always exclude suspended (excluded_from_rates)
# ----------------------------------------------------------------------
def rate_denominator(acc: pd.DataFrame) -> pd.DataFrame:
    """Accounts eligible for rate denominators (suspended removed, per definitions)."""
    return acc[~acc["excluded_from_rates"]]

def status_rates(df: pd.DataFrame) -> dict:
    """Closure / discontinuation / churn / retention rates on a rate-eligible frame."""
    n = len(df)
    if n == 0:
        return dict(n=0, closure=np.nan, discontinuation=np.nan,
                    churn_strict=np.nan, churn_broad=np.nan, retention=np.nan)
    closed = (df["status"] == "closed").sum()
    disc = (df["status"] == "discontinued").sum()
    inactive = (df["status"] == "inactive").sum()
    active = (df["status"] == "active").sum()
    return dict(
        n=int(n),
        closure=closed / n,
        discontinuation=disc / n,
        churn_strict=(closed + disc) / n,
        churn_broad=(closed + disc + inactive) / n,
        retention=active / n,        # active share (snapshot)
    )

# ----------------------------------------------------------------------
# Banding (re-derive from yaml so notebooks never hardcode cutoffs)
# ----------------------------------------------------------------------
def band(value, bands_list, label_key="label", lo="min", hi="max"):
    """Left-closed [min,max) banding matching Agent 1's convention."""
    if pd.isna(value):
        return pd.NA
    for b in bands_list:
        if b[lo] <= value < b[hi]:
            return b[label_key]
    return pd.NA

# ----------------------------------------------------------------------
# Plotting style -- presentation-ready, consistent across sections
# ----------------------------------------------------------------------
FUND_SHORT = {
    "Apex Fixed Income Fund": "Fixed Income",
    "Apex Shariah Growth Fund": "Shariah Growth",
    "Apex Balanced Opportunity Fund": "Balanced Opp.",
    "Apex Capital Growth Fund": "Capital Growth",
}
FUND_COLORS = {
    "Apex Fixed Income Fund": "#2E5A87",
    "Apex Shariah Growth Fund": "#3E8E7E",
    "Apex Balanced Opportunity Fund": "#C9913B",
    "Apex Capital Growth Fund": "#9A3B5B",
}

def set_style():
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    mpl.rcParams.update({
        "figure.dpi": 110,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linestyle": "-",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    })

def taka(x, decimals=1):
    """Format a BDT amount in lakh/crore-aware compact notation."""
    try:
        x = float(x)
    except (TypeError, ValueError):
        return str(x)
    a = abs(x)
    sign = "-" if x < 0 else ""
    if a >= 1e7:
        return f"{sign}৳{x/1e7:,.{decimals}f} Cr"
    if a >= 1e5:
        return f"{sign}৳{x/1e5:,.{decimals}f} L"
    if a >= 1e3:
        return f"{sign}৳{x/1e3:,.{decimals}f}k"
    return f"{sign}৳{x:,.0f}"

def savefig(fig, section_dir: str, name: str):
    """Save PNG to the section's figures folder; return relative path."""
    out = ANALYSIS / section_dir / "figures"
    out.mkdir(parents=True, exist_ok=True)
    p = out / f"{name}.png"
    fig.savefig(p)
    return str(p.relative_to(REPO)).replace("\\", "/")

def save_table(df: pd.DataFrame, section_dir: str, name: str, index=True):
    """Save a metric table as CSV under the section folder; return relative path."""
    out = ANALYSIS / section_dir / "tables"
    out.mkdir(parents=True, exist_ok=True)
    p = out / f"{name}.csv"
    df.to_csv(p, index=index)
    return str(p.relative_to(REPO)).replace("\\", "/")

def dump_metrics(section_dir: str, metrics: dict):
    """Persist a section's headline numbers as JSON for Gate 2 to recompute against."""
    out = ANALYSIS / section_dir
    out.mkdir(parents=True, exist_ok=True)
    p = out / "_metrics.json"
    with open(p, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, default=str)
    return str(p.relative_to(REPO)).replace("\\", "/")
