"""17-nov · (1) TIR requerida en UF y (2) riesgo cambiario: EE.UU. vs. fuera de EE.UU. medido en UF.

Uso: python3 a_tir_uf_y_moneda.py RUTA_CODIGO_M12   (carpeta 'codigo' del modelo 12-nov de Matías; usa sus datos)
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, sys.argv[1])
import datos as D
from objetivos import pagos_educacion, tir
from m12_config import *
from scipy.optimize import brentq

# ---------- 1. TIR en UF ----------
# Flujos en UF: capital y aportes son dólares que se convierten a UF al tipo de cambio real de cada año.
# g = tendencia real anual del dólar frente a la UF (0 = paridad de poder de compra, supuesto del modelo).
def flujos_uf(g):
    q = lambda t: (1 + g) ** t / USD_UF0                       # UF que compra 1 USD real en el año t
    cf = np.zeros(ANO_HERENCIA + 1); cf[0] = INV * q(0)
    for t in range(1, N_APORTES + 1): cf[t] += APORTE * q(t)
    for y, v in pagos_educacion().items(): cf[y] -= v / USD_UF0           # Educación: fija en UF
    cf[ANO_VILLARRICA] -= VILLARRICA_UF                                    # Villarrica: fija en UF
    cf[ANO_HERENCIA] -= HERENCIA_USD * q(ANO_HERENCIA)                    # herencia: USD reales → UF del año 50
    return cf
irr = lambda cf: brentq(lambda r: sum(v / (1 + r) ** t for t, v in enumerate(cf)), -0.5, 0.5)
tir_tab = pd.DataFrame([{"Supuesto dólar real vs UF": lab, "TIR requerida en UF": irr(flujos_uf(g))}
                        for lab, g in [("Dólar pierde 1% real al año", -0.01), ("Constante (PPC, supuesto base)", 0.0),
                                       ("Dólar gana 1% real al año", 0.01)]])
cf0 = flujos_uf(0.0)
print("TIR en UF\n", tir_tab.round(4).to_string(index=False))
print("Capital invertido UF %.0f; aporte anual UF %.0f; Educación total UF %.0f" % (cf0[0], APORTE / USD_UF0, sum(pagos_educacion().values()) / USD_UF0))

# ---------- 2. Riesgo cambiario medido en UF ----------
c = D.mensual(D.etf_nucleo()); x = D.mensual(D.etf_extra())
ad = pd.read_parquet(os.path.join(DATOS, "acwi_djp_prices.parquet")).resample("ME").last().pct_change()
fx = x["CLP=X"].where(x["CLP=X"].abs() < 0.5)  # variación mensual USD/CLP
ufp = pd.read_csv(os.path.join(DATOS, "uf_diaria_sii.csv"), index_col=0, parse_dates=True)["UF"]
uf = ufp.resample("ME").last().pct_change()
idx = c.loc["2013-02-28":"2026-08-31"].index
en_uf = lambda r: ((1 + r) * (1 + fx) / (1 + uf) - 1).reindex(idx)
filas = []
for lab, r in [("S&P 500 (SPY)", c.SPY), ("Mundo sin EE.UU. desarrollado (EFA)", x.EFA), ("Mundo (ACWI)", ad.ACWI)]:
    r = r.reindex(idx); u = en_uf(r)
    dd = lambda s: ((1 + s).cumprod() / (1 + s).cumprod().cummax() - 1).min()
    filas.append({"Activo": lab, "Vol. en USD": r.std() * 12 ** .5, "Vol. en UF": u.std() * 12 ** .5,
                  "Corr. con USD/CLP": r.corr(fx.reindex(idx)), "Peor caída en UF": dd(u), "Corr. con SPY (USD)": r.corr(c.SPY.reindex(idx))})
fxv = pd.DataFrame(filas)
# EFA explicado por el S&P 500: lo que no explica es riesgo de otros países + otras monedas (EUR, JPY, GBP...)
e = x.EFA.reindex(idx); s = c.SPY.reindex(idx); b = e.cov(s) / s.var(); res = e - b * s
extra = {"Beta EFA vs SPY": b, "R² EFA vs SPY": e.corr(s) ** 2, "Vol. no explicada por EE.UU. (anual)": res.std() * 12 ** .5}
print("\nRiesgo cambiario (2013-2026, mensual)\n", fxv.round(3).to_string(index=False)); print(extra)
os.makedirs(os.path.join(BASE, "resultados"), exist_ok=True)
pd.to_pickle({"tir_uf": tir_tab, "flujos_uf": cf0, "moneda": fxv, "efa_vs_spy": extra}, os.path.join(BASE, "resultados", "a_tir_uf_moneda.pkl"))
