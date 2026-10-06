"""Validación: robustez de parámetros, subperíodos, walk-forward, costos y sesgos del modelo original."""
import numpy as np
import pandas as pd
import estrategias as E
import portafolio as PF
import datos as D
from config import ACTIVOS, PESOS_APROBADOS, INICIO_EVAL, FIN_DATOS

def _stats(r, bil):
    r = r.loc[INICIO_EVAL:FIN_DATOS].dropna(); b = bil.reindex(r.index).fillna(0)
    sh = lambda x, y: (x - y).mean() * 12 / (x.std() * np.sqrt(12)); w = (1 + r).cumprod()
    a, z = r.loc[:"2019-12-31"], r.loc["2020-01-01":]
    return {"CAGR": w.iloc[-1] ** (12 / len(r)) - 1, "Volatilidad": r.std() * np.sqrt(12), "Sharpe": sh(r, b),
            "Máx. caída": (w / w.cummax() - 1).min(), "Sharpe 2013-2019": sh(a, b.reindex(a.index)), "Sharpe 2020-2026": sh(z, b.reindex(z.index))}

def robustez():
    bil = D.mensual(D.etf_nucleo())["BIL"]; N = -9.0
    grid = [("Momentum", "BASE (vigente)", E.momentum_acciones, {}),
            ("Momentum", "Sin filtros absolutos (solo ranking)", E.momentum_acciones, dict(th_r3=N, th_r6=N, th_r12=N, sharpe_min=N)),
            ("Momentum", "Umbrales x2 (r6>10%, r12>20%)", E.momentum_acciones, dict(th_r6=.10, th_r12=.20)),
            ("Momentum", "Sin filtro de Sharpe", E.momentum_acciones, dict(sharpe_min=N)),
            ("Momentum", "Top 15", E.momentum_acciones, dict(top_n=15)),
            ("Momentum", "Top 20", E.momentum_acciones, dict(top_n=20)),
            ("Momentum", "Límite sectorial 30%", E.momentum_acciones, dict(max_sector=.30)),
            ("Momentum", "Sin límite sectorial", E.momentum_acciones, dict(max_sector=1.0)),
            ("Low-Volatility", "BASE (vigente)", E.low_volatility, {}),
            ("Low-Volatility", "Top 15", E.low_volatility, dict(top_n=15)),
            ("Low-Volatility", "Top 20", E.low_volatility, dict(top_n=20)),
            ("Low-Volatility", "Límite sectorial 30%", E.low_volatility, dict(max_sector=.30)),
            ("Low-Volatility", "Sin límite sectorial", E.low_volatility, dict(max_sector=1.0)),
            ("Commodities", "BASE (vigente, 5 ETF)", E.momentum_commodities, {}),
            ("Commodities", "Universo original 3 ETF (GLD, USO, DBA)", E.momentum_commodities, dict(universo=["GLD", "USO", "DBA"])),
            ("Commodities", "Umbrales a la mitad", E.momentum_commodities, dict(th_r3=.025, th_r6=.04, th_r12=.05)),
            ("Commodities", "Umbrales en cero (solo tendencia)", E.momentum_commodities, dict(th_r3=0, th_r6=0, th_r12=0)),
            ("Commodities", "Sin límite de volatilidad", E.momentum_commodities, dict(vol_max=9.0))]
    rows = []
    for est, lab, fn, kw in grid:
        r = fn(**kw)["retorno"]; rows.append({"Estrategia": est, "Variante": lab, **_stats(r, bil)}); print(est, lab, flush=True)
    return pd.DataFrame(rows)

def walk_forward(df, bil):
    ins, oos = df.loc[:"2019-12-31"], df.loc["2020-01-01":]
    mk = PF.markowitz(ins)["w"]; bl = PF.black_litterman(ins)["w"]
    out = []
    for lab, w in [("Markowitz optimizado con 2013-2019", mk), ("Black-Litterman calibrado con 2013-2019", bl),
                   ("Pesos aprobados (BL del modelo)", pd.Series(PESOS_APROBADOS)), ("Pesos iguales (1/6)", pd.Series(1 / 6, ACTIVOS))]:
        for per, d in [("Dentro de muestra 2013-2019", ins), ("Fuera de muestra 2020-2026", oos)]:
            r = (d * w).sum(axis=1); m = PF.metricas(r, bil, d.SPY)
            out.append({"Cartera": lab, "Período": per, "CAGR": m["CAGR"], "Volatilidad": m["Volatilidad"], "Sharpe": m["Sharpe"], "Máx. caída": m["Máx. caída"],
                        **{f"w {a}": w[a] for a in ACTIVOS}})
    return pd.DataFrame(out)
