"""Carga de datos (caché local en /datos; descarga desde Yahoo Finance solo si falta)."""
import os
import numpy as np
import pandas as pd
from config import DATOS, FIN_DATOS

def _p(n): return os.path.join(DATOS, n)

def membresia():
    m = pd.read_csv(_p("sp500_membership.csv")); m["date"] = pd.to_datetime(m["date"]); return m

def universo_en(m, fecha):
    """Constituyentes del S&P 500 vigentes a la fecha (point-in-time)."""
    sub = m[m["date"] <= fecha]
    return set(sub.iloc[-1]["tickers"].split(",")) if len(sub) else set()

def precios_sp500():
    p = pd.read_parquet(_p("sp500_prices.parquet")).loc[:FIN_DATOS]
    v = pd.read_parquet(_p("sp500_volumes.parquet")).reindex(p.index)
    return p, v

def etf_nucleo():
    return pd.read_parquet(_p("core_etf_prices.parquet"))

def sectores():
    s = pd.read_csv(_p("sector_map.csv")); return dict(zip(s["Symbol"], s["GICS Sector"]))

EXTRA = ["QMOM", "SPLV", "USMV", "EFA", "AGG", "BNDX", "BNDW", "CLP=X", "DJP"]   # DJP: Bloomberg Commodity Index TR (ETN), desde oct-2026
def etf_extra():
    f = _p("extra_prices.parquet")
    if os.path.exists(f): return pd.read_parquet(f)
    import yfinance as yf
    d = yf.download(EXTRA, start="2009-01-01", end="2026-09-01", progress=False, auto_adjust=True)["Close"]
    d.to_parquet(f); return d

def mensual(px):
    return px.resample("ME").last().pct_change(fill_method=None)
