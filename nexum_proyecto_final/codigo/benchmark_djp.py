"""Cambio de benchmark de commodities (oct-2026): de la mezcla de los 5 ETF a DJP (Bloomberg Commodity Index TR).

Recalcula solo lo que depende del benchmark (secciones 4 y 5 de run_all.py) sobre los retornos oficiales guardados
en resultados/estado.pkl, sin volver a correr los backtests: así las estrategias, Black-Litterman y el Montecarlo
quedan exactamente como en la versión oficial. run_all.py ya usa DJP para una corrida completa.
Uso: python3 benchmark_djp.py   (después: analisis_adicional.py, excel_modelo.py, figuras.py, informe.py)
"""
import os
import numpy as np
import pandas as pd
import datos as D, portafolio as PF
from config import *

f = os.path.join(RESULTADOS, "estado.pkl"); S = pd.read_pickle(f); T = S["T"]; df = S["df"]
c = D.mensual(D.etf_nucleo()); x = D.mensual(D.etf_extra()); bil = c.BIL; W = pd.Series(PESOS_APROBADOS)

# Sección 4 de run_all.py: benchmark de política, métricas y tracking error
port = (df * W).sum(axis=1); bser = PF.benchmark_series(df.index); bench = (bser * W).sum(axis=1); agf = S["agf"]
w16 = df.loc[INICIO_BENCH:].index
met = []
for per, idx in [("2016-2026", w16), ("2013-2026", df.index)]:
    for lab, r in [("Cartera Nexum", port), ("Benchmark de política", bench), ("Cartera actual AGF 85/15", agf), ("S&P 500 (SPY)", df.SPY)]:
        if per == "2013-2026" and lab == "Benchmark de política": continue
        met.append({"Período": per, "Serie": lab, **PF.metricas(r.loc[idx], bil, df.SPY, bench.loc[w16] if per == "2016-2026" else None)})
T["Metricas"] = pd.DataFrame(met)
act = (port - bench).loc[w16]
sleeve_te = {a: ((df[a] - bser[a]).loc[w16].std() * np.sqrt(12)) for a in ACTIVOS}
T["Tracking_error"] = pd.DataFrame([{"Concepto": "TE ex-ante, pesos aprobados (2016-2026)", "Valor": act.std() * np.sqrt(12)},
    {"Concepto": "TE últimos 36 meses", "Valor": act.iloc[-36:].std() * np.sqrt(12)},
    {"Concepto": "Alfa objetivo anual", "Valor": ALFA_OBJETIVO}, {"Concepto": "Information ratio objetivo", "Valor": IR_OBJETIVO},
    {"Concepto": "TE objetivo = alfa / IR", "Valor": ALFA_OBJETIVO / IR_OBJETIVO}, {"Concepto": "TE máximo (alfa 2% / IR 0,5)", "Valor": TE_MAX}]
    + [{"Concepto": f"TE del sleeve {NOMBRES[a]} vs su benchmark", "Valor": v} for a, v in sleeve_te.items()])
pd.DataFrame({"Cartera": port, "Benchmark": bench, "AGF": agf, "SPY": df.SPY}).to_csv(os.path.join(RESULTADOS, "retornos_cartera_benchmark.csv"))

# Sección 5 de run_all.py: estrategias frente a su benchmark
est = []
for a, b in [("MOM_EQ", "QMOM"), ("LOW_VOL", "SPLV"), ("MOM_CMD", "DJP")]:
    est.append({"Estrategia": NOMBRES[a], "Benchmark": b, **PF.metricas(df[a].loc[w16], bil, df.SPY, bser[a].loc[w16])})
    est.append({"Estrategia": NOMBRES[a] + " (2013-2026)", "Benchmark": "—", **PF.metricas(df[a], bil, df.SPY)})
T["Estrategias"] = pd.DataFrame(est)

S.update({"bench": bench, "bser": bser}); pd.to_pickle(S, f)
with pd.ExcelWriter(os.path.join(RESULTADOS, "resultados_modelo.xlsx")) as xw:
    for k, t in T.items(): t.to_excel(xw, sheet_name=k[:31], index=k == "Covarianza_anual")
if __name__ == "__main__":
    pd.set_option("display.width", 220)
    for k in ["Metricas", "Tracking_error", "Estrategias"]: print(f"\n{k}\n", T[k].round(4).to_string(index=False))
