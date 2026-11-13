"""Backtest con el costo real de StockTrak: comisión fija de USD 10 por orden (retroalimentación P2, criterio A3).

El modelo aprobado descontaba 0,1% del monto transado. En StockTrak la comisión es fija (USD 10 por orden), así que el
costo pesa más en las estrategias con posiciones chicas. Aquí cada mes se cuentan las órdenes de cada satélite
(entradas + salidas de títulos) y se cobra USD 10 por orden sobre el capital del satélite (peso aprobado x USD 150.000).

Además mide la cartera en CLP, la moneda funcional definida en el IPS (retorno en USD + variación del dólar observado).
Salida: resultados/costos_stocktrak.pkl y resultados/costos_stocktrak.csv. Uso: python3 costos_stocktrak.py (≈2 min)
"""
import os
import numpy as np
import pandas as pd
import datos as D, estrategias as E, portafolio as PF, montecarlo as MC
from config import *

COMISION = 10.0                                    # USD por orden en StockTrak
SATELITES = {"MOM_EQ": E.momentum_acciones, "LOW_VOL": E.low_volatility, "MOM_CMD": E.momentum_commodities}
W = pd.Series(PESOS_APROBADOS)

def costo_fijo(capital):
    """Costo como fracción del satélite: USD 10 por cada título que entra o sale."""
    def f(prev, new):
        ordenes = len(set(new) - set(prev)) + len(set(prev) - set(new))
        return ordenes * COMISION / capital
    return f

orig = E._costo
rets, ordenes = {}, {}
for k, fn in SATELITES.items():
    cap = W[k] * CAPITAL
    E._costo = costo_fijo(cap)
    g = {}; rets[k] = fn(guardar=g)["retorno"]
    fechas = sorted(g); n = [len(set(g[b]) ^ set(g[a])) for a, b in zip(fechas[:-1], fechas[1:])]
    ordenes[k] = pd.Series(n, index=fechas[1:])
E._costo = orig
base = {"MOM_EQ": E.momentum_acciones()["retorno"], "LOW_VOL": E.low_volatility()["retorno"], "MOM_CMD": E.momentum_commodities()["retorno"]}

c = D.mensual(D.etf_nucleo()); bil = c.BIL
df0 = PF.tabla_retornos(base); df1 = PF.tabla_retornos(rets)
bser = PF.benchmark_series(df1.index)
fxp = D.etf_extra()["CLP=X"]; fxp = fxp[fxp > 100]
fx = fxp.resample("ME").last().pct_change().reindex(df1.index)          # variación del dólar observado (CLP por USD)

x = D.mensual(D.etf_extra())
CLASES = {"RV": (["SPY", "LOW_VOL", "MOM_EQ"], c.SPY), "RF": (["TLH", "VCLT"], 0.5 * c.TLH + 0.5 * c.VCLT), "CMD": (["MOM_CMD"], x.DJP)}
comp = sum(W[a].sum() * b.reindex(df1.index) for a, b in CLASES.values())   # benchmark oficial por clase de activo

filas = []
for per, ini in [("2016-2026", INICIO_BENCH), ("2013-2026", INICIO_EVAL)]:
    for costo, d in [("0,1% del monto (modelo aprobado)", df0), ("USD 10 por orden (StockTrak)", df1)]:
        port = (d * W).sum(axis=1)
        for mon in ["USD", "CLP"]:
            p = port if mon == "USD" else (1 + port) * (1 + fx) - 1
            b = comp if mon == "USD" else (1 + comp) * (1 + fx) - 1
            idx = p.loc[ini:].dropna().index.intersection(b.dropna().index)
            m = PF.metricas(p.loc[idx], bil, c.SPY, b.loc[idx]); mb = PF.metricas(b.loc[idx], bil, c.SPY)
            filas.append({"Período": per, "Costo": costo, "Moneda": mon, "CAGR Nexum": m["CAGR"], "CAGR benchmark": mb["CAGR"],
                          "Vol. Nexum": m["Volatilidad"], "Vol. benchmark": mb["Volatilidad"], "Máx. caída Nexum": m["Máx. caída"],
                          "Máx. caída benchmark": mb["Máx. caída"], "Sharpe (rf T-Bills, solo USD)": m["Sharpe"] if mon == "USD" else np.nan,
                          "Beta vs S&P 500": m["Beta"], "Tracking error": m["Tracking error"], "Information ratio": m["Information ratio"]})
res = pd.DataFrame(filas)

estr = []
for k in SATELITES:
    for lab, s in [("0,1%", df0[k]), ("USD 10/orden", df1[k])]:
        s = s.loc[INICIO_BENCH:]; estr.append({"Estrategia": k, "Costo": lab, "CAGR": (1 + s).prod() ** (12 / len(s)) - 1,
                                               "Volatilidad": s.std() * np.sqrt(12)})
    o = ordenes[k].loc[INICIO_BENCH:]
    estr.append({"Estrategia": k, "Costo": "órdenes por mes (prom.)", "CAGR": o.mean(), "Volatilidad": np.nan})
estr = pd.DataFrame(estr)

# Montecarlo con la serie corregida por costos (metas en UF; herencia en USD reales convertida al tipo de cambio del escenario)
fxl = np.log(fxp.resample("ME").last()).diff().reindex(df1.index); fx_d = fxl - fxl.mean()
real = {a: MC.deflactar(df1[a]) for a in ACTIVOS}; fwd = {a: MC.ajustar_media(real[a], CMA[a]) for a in ACTIVOS}
mc = []
for esc, s in [("Histórico 2013-2026", sum(W[a] * real[a] for a in ACTIVOS)), ("Prudente", sum(W[a] * fwd[a] for a in ACTIVOS))]:
    for mon, z in [("USD", None), ("UF", fx_d)]:
        r = MC.simular(s, z); mc.append({"Escenario": esc, "Moneda de las metas": mon, **{k: v for k, v in r.items() if k.startswith("P(")}})
mc = pd.DataFrame(mc)

pd.to_pickle({"metricas": res, "estrategias": estr, "montecarlo": mc, "ordenes": ordenes}, os.path.join(RESULTADOS, "costos_stocktrak.pkl"))
res.to_csv(os.path.join(RESULTADOS, "costos_stocktrak.csv"), index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(res.round(4).to_string(index=False)); print(estr.round(4).to_string(index=False)); print(mc.round(4).to_string(index=False))
