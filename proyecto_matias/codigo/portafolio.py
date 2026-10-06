"""Asignación estratégica: datos mensuales comunes, Markowitz histórico, Black-Litterman, benchmark y métricas."""
import numpy as np
import pandas as pd
from scipy.optimize import minimize
import datos as D
from config import (ACTIVOS, INICIO_EVAL, FIN_DATOS, NUCLEO_MIN, NUCLEO_MAX, PISO_BONOS, BL_DELTA, BL_TAU, BL_VISTAS, BENCH)

def tabla_retornos(series_activas):
    """Retornos mensuales nominales USD de los 6 activos, ventana común 2013-01..2026-08."""
    c = D.mensual(D.etf_nucleo())
    df = pd.DataFrame({"SPY": c.SPY, "TLH": c.TLH, "VCLT": c.VCLT, "MOM_CMD": series_activas["MOM_CMD"],
                       "MOM_EQ": series_activas["MOM_EQ"], "LOW_VOL": series_activas["LOW_VOL"]})
    return df.loc[INICIO_EVAL:FIN_DATOS].dropna()

def _restricciones(pisos):
    c = [{"type": "eq", "fun": lambda x: x.sum() - 1},
         {"type": "ineq", "fun": lambda x: x[:3].sum() - NUCLEO_MIN}, {"type": "ineq", "fun": lambda x: NUCLEO_MAX - x[:3].sum()}]
    if pisos: c += [{"type": "ineq", "fun": lambda x: x[1] - PISO_BONOS}, {"type": "ineq", "fun": lambda x: x[2] - PISO_BONOS}]
    return c

def max_sharpe(mu, S, pisos, x0s):
    f = lambda x: -(x @ mu) / np.sqrt(x @ S @ x)
    best = min((minimize(f, x0, bounds=[(0, 1)] * len(mu), constraints=_restricciones(pisos), method="SLSQP", options={"ftol": 1e-12, "maxiter": 1000}) for x0 in x0s), key=lambda o: o.fun)
    return best.x, -best.fun

def markowitz(df):
    mu, S = df.mean().values * 12, df.cov().values * 12
    w, sh = max_sharpe(mu, S, True, [np.ones(6) / 6, np.array([.48, .08, .08, .18, .02, .16])])
    return dict(w=pd.Series(w, ACTIVOS), sharpe=sh, mu=pd.Series(mu, ACTIVOS), S=pd.DataFrame(S, ACTIVOS, ACTIVOS))

def black_litterman(df):
    S = df.cov().values * 12; vol = np.sqrt(np.diag(S))
    w_eq = (1 / vol) / (1 / vol).sum()                       # prior de paridad de riesgo (inverso de volatilidad)
    pi = BL_DELTA * S @ w_eq
    P = np.array([[v.get(a, 0.0) for a in ACTIVOS] for _, v, _, _ in BL_VISTAS]); Q = np.array([q for _, _, q, _ in BL_VISTAS])
    tS = BL_TAU * S; Om = np.diag(np.diag(P @ tS @ P.T))     # Ω proporcional a la varianza de cada vista (He-Litterman)
    A = np.linalg.inv(np.linalg.inv(tS) + P.T @ np.linalg.inv(Om) @ P)
    mu = A @ (np.linalg.inv(tS) @ pi + P.T @ np.linalg.inv(Om) @ Q)
    w, sh = max_sharpe(mu, S, False, [np.ones(6) / 6, w_eq])
    return dict(w=pd.Series(w, ACTIVOS), sharpe=sh, w_eq=pd.Series(w_eq, ACTIVOS), pi=pd.Series(pi, ACTIVOS),
                mu_bl=pd.Series(mu, ACTIVOS), S=pd.DataFrame(S, ACTIVOS, ACTIVOS), P=P, Q=Q, Omega=Om)

def benchmark_series(idx):
    c = D.mensual(D.etf_nucleo()); x = D.mensual(D.etf_extra())
    comp = {"SPY": c.SPY, "TLH": c.TLH, "VCLT": c.VCLT, "QMOM": x.QMOM, "SPLV": x.SPLV,
            "MEZCLA_CMD": c[["GLD", "USO", "DBA", "SLV", "CPER"]].mean(axis=1)}
    return pd.DataFrame({a: comp[BENCH[a]] for a in ACTIVOS}).reindex(idx)

def metricas(r, rf, mkt, b=None):
    r, rf, mkt = r.dropna(), rf.reindex(r.dropna().index), mkt.reindex(r.dropna().index)
    ex = r - rf; w = (1 + r).cumprod(); dd = (w / w.cummax() - 1).min(); cagr = w.iloc[-1] ** (12 / len(r)) - 1
    beta = np.cov(r, mkt)[0, 1] / mkt.var(); down = ex[ex < 0]
    out = {"CAGR": cagr, "Volatilidad": r.std() * np.sqrt(12), "Sharpe": ex.mean() * 12 / (r.std() * np.sqrt(12)),
           "Sortino": ex.mean() * 12 / (np.sqrt((down ** 2).mean()) * np.sqrt(12)), "Beta": beta,
           "Treynor": ex.mean() * 12 / beta, "Alfa CAPM": (ex.mean() - beta * (mkt - rf).mean()) * 12,
           "Máx. caída": dd, "Calmar": cagr / abs(dd), "VaR 95% mensual": -np.percentile(r, 5),
           "CVaR 95% mensual": -r[r <= np.percentile(r, 5)].mean(), "Meses": len(r)}
    if b is not None:
        a = (r - b.reindex(r.index)).dropna(); te = a.std() * np.sqrt(12)
        out.update({"Tracking error": te, "Information ratio": a.mean() * 12 / te if te > 0 else np.nan})
    return out
