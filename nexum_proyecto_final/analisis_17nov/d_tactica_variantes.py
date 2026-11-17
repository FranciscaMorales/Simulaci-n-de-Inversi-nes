"""17-nov · Variantes de la regla táctica de tendencia (10 meses): a dónde va el peso cuando la señal es negativa.
Uso: python3 d_tactica_variantes.py RUTA_CODIGO_M12"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, sys.argv[1])
import datos as D
import m12_cartera as K
from m12_config import *
p = K.cartera(W_A); c = K.C
px = D.etf_nucleo()[["SPY", "TLH", "VCLT"]].resample("ME").last()
sig = lambda s: (px[s] > px[s].rolling(10).mean()).shift(1).reindex(K.IDX).fillna(True).astype(bool)
sS, sT = sig("SPY"), sig("TLH")
n = c[["SPY", "TLH", "VCLT", "BIL"]].reindex(K.IDX); bonos = 0.5 * n.TLH + 0.5 * n.VCLT
def correr(lab, delta):          # delta: DataFrame de cambios de peso (suman 0) sobre SPY, BONOS, BIL
    act = delta.SPY * n.SPY + delta.BONOS * bonos + delta.BIL * n.BIL
    ordenes = (delta.diff().abs() > 1e-9).sum(axis=1) + (delta.BONOS.diff().abs() > 1e-9)   # bonos = 2 órdenes (TLH y VCLT)
    r = (p["neto"].reindex(K.IDX) + act - COMISION * ordenes / INV).dropna(); m = K.metricas(r, K.benchmark(W_A))
    return {"Regla": lab, "Retorno anual": m["Retorno anual"], "Volatilidad": m["Volatilidad"], "Máx. caída": m["Máx. caída"], "TE": m["Tracking error"],
            "IR": m["Information ratio"], "Sharpe": m["Sharpe"], "Órdenes extra/año": ordenes.sum() / (len(K.IDX) / 12),
            "Retorno 2022": (1 + r.loc["2022"]).prod() - 1, "Retorno 2020": (1 + r.loc["2020"]).prod() - 1}
f = []
z = pd.Series(0.0, index=K.IDX)
f.append(correr("Sin táctica (vigente)", pd.DataFrame({"SPY": z, "BONOS": z, "BIL": z})))
for t in [0.05, 0.10]:
    d = np.where(sS, t, -t); f.append(correr(f"A · acciones ↔ bonos ±{t:.0%}", pd.DataFrame({"SPY": d, "BONOS": -d, "BIL": 0.0}, index=K.IDX)))
    f.append(correr(f"B · acciones → caja si tendencia negativa (−{t:.0%})", pd.DataFrame({"SPY": np.where(sS, 0, -t), "BONOS": 0.0, "BIL": np.where(sS, 0, t)}, index=K.IDX)))
    dS = np.where(sS, 0, -t); dB = np.where(sT, 0, -t)
    f.append(correr(f"C · cada clase a caja si su tendencia es negativa (−{t:.0%} c/u)", pd.DataFrame({"SPY": dS, "BONOS": dB, "BIL": -(dS + dB)}, index=K.IDX)))
T = pd.DataFrame(f); print(T.round(4).to_string(index=False))
print("Meses con tendencia negativa: S&P 500 %.0f%%, Tesoro largo %.0f%%" % (100 * (~sS).mean(), 100 * (~sT).mean()))
pd.to_pickle(T, os.path.join(BASE, "resultados", "d_tactica.pkl"))
