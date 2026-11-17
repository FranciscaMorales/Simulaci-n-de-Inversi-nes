"""17-nov · Cálculos para la defensa, sobre el modelo 12-nov de Matías (sin modificarlo).
  1. AGF con su comisión (TAC) en el Montecarlo, frente a Nexum y al benchmark pasivo.
  2. Presupuesto de tracking error dentro de los techos del IPS (vol. 12%, caída 25%) y TE óptimo según la aversión A.
  3. Estrés: año tipo 2022 (acciones y bonos caen juntos) al inicio y justo antes de Educación; prueba de estrés inversa.
  4. Asignación táctica: tendencia de 10 meses (Faber, 2007) para inclinar renta variable vs. bonos ±5/±10 pp.
Uso: python3 c_defensa_calculos.py RUTA_CODIGO_M12   (≈10 min)
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, sys.argv[1])
import datos as D
import montecarlo as MC0
import m12_cartera as K
import m12_montecarlo as M
from m12_config import *

R = {}; cols = ["P(Educación)", "P(Villarrica)", "P(Herencia)", "P(3 objetivos)"]
q = lambda r: {k: r[k] for k in cols}
hist, pros, ords = M.series_cartera(W_A)

# ---------- 1. AGF con TAC ----------
c, x = K.C, K.X; agfb = 0.5 * x.AGG + 0.5 * x.BNDX
ar = {"SPY": MC0.deflactar(c.SPY).reindex(K.IDX), "EFA": MC0.deflactar(x.EFA).reindex(K.IDX), "BONOS_GLOBAL": MC0.deflactar(agfb).reindex(K.IDX)}
agf_p = sum(AGF[k] * MC0.ajustar_media(ar[k].dropna(), CMA[k]).reindex(K.IDX) for k in AGF)
pc = K.pesos_clase(W_A)
bc = {"RV": (c.SPY, CMA["SPY"]), "RF": (0.5 * c.TLH + 0.5 * c.VCLT, 0.5 * CMA["TLH"] + 0.5 * CMA["VCLT"]), "CMD": (K.AD["DJP"], CMA["MOM_CMD"])}
ben_p = sum(pc[k] * MC0.ajustar_media(MC0.deflactar(v[0]).reindex(K.IDX), v[1]) for k, v in bc.items())
filas = [{"Cartera": "Nexum vigente (USD 10 por orden)", "Costo": f"{ords:.0f} órdenes/año ≈ {ords*COMISION/INV:.2%}", **q(M.simular(pros, "META", ordenes_ano=ords))},
         {"Cartera": "Nexum vigente sin comisiones", "Costo": "0", **q(M.simular(pros, "META"))},
         {"Cartera": "Benchmark pasivo (ETF, 18 órdenes/año)", "Costo": "≈0,13%", **q(M.simular(ben_p, "META", ordenes_ano=18))}]
for tac in [0.0, 0.0109, 0.0147, 0.0161, 0.021]:
    filas.append({"Cartera": "AGF 85/15", "Costo": f"TAC {tac:.2%}", **q(M.simular(agf_p, "META", dr=-tac))})
R["agf"] = pd.DataFrame(filas); print(R["agf"].round(3).to_string(index=False), flush=True)

# ---------- 2. Presupuesto de TE y TE óptimo ----------
p = K.cartera(W_A); b = K.benchmark(W_A).reindex(K.IDX); a = (p["neto"] - b).dropna(); b = b.reindex(a.index)
filas = []
for k in np.arange(0, 6.01, 0.25):
    r = b + k * a; w = (1 + r).cumprod()
    filas.append({"Escala de apuestas activas": k, "TE": (k * a).std() * 12 ** .5, "Volatilidad": r.std() * 12 ** .5, "Máx. caída": (w / w.cummax() - 1).min()})
pres = pd.DataFrame(filas); R["presupuesto"] = pres
lim_vol = pres[pres.Volatilidad <= 0.12]["TE"].max(); lim_dd = pres[pres["Máx. caída"] >= -0.25]["TE"].max()
rf = K.BIL.reindex(a.index); ex = p["neto"].reindex(a.index) - rf
A_impl = ex.mean() * 12 / (p["neto"].reindex(a.index).std() ** 2 * 12)
R["te_limites"] = {"TE actual": a.std() * 12 ** .5, "TE máx. con vol ≤ 12%": lim_vol, "TE máx. con caída ≥ −25%": lim_dd,
                   "corr(activo, benchmark)": a.corr(b), "A implícita de la cartera (hist.)": A_impl}
print(pres.round(4).to_string(index=False)); print(R["te_limites"], flush=True)
# TE óptimo: U = E − ½A·σ²; con α = IR·ω y apuestas no correlacionadas con el benchmark, ω* = IR / A (Grinold y Kahn)
R["te_optimo"] = pd.DataFrame([{"A": A, "IR esperado": ir, "TE óptimo": ir / A} for A in [2.5, 5.5, 9.0] for ir in [0.2, 0.35, 0.5]])
print(R["te_optimo"].round(4).to_string(index=False), flush=True)

# ---------- 3. Estrés ----------
X = pd.concat([pros, M.F.qd, M.F.ufd], axis=1).dropna(); pos22 = [X.index.get_loc(t) for t in X.index if t.year == 2022]
orig = M._indices
def forzar(meses_ini):
    def f(T, n, rng, bloque):
        I = orig(T, n, rng, bloque)
        for m0 in meses_ini: I[:, m0:m0 + 12] = pos22
        return I
    return f
filas = [{"Escenario": "Base prospectivo", **q(M.simular(pros, "META", ordenes_ano=ords))}]
for lab, ini in [("2022 en el año 1", [0]), ("2022 en el año 13 (justo antes de Educación)", [12 * 12]), ("2022 en el año 24 (antes de Villarrica)", [23 * 12]),
                 ("2022 en los años 1 y 13", [0, 12 * 12])]:
    M._indices = forzar(ini); filas.append({"Escenario": lab, **q(M.simular(pros, "META", ordenes_ano=ords))})
M._indices = orig
r22 = pros.loc["2022"]; filas.append({"Escenario": f"(retorno real de la cartera en 2022: {(1 + r22).prod() - 1:.1%})"})
R["estres_2022"] = pd.DataFrame(filas); print(R["estres_2022"].round(3).to_string(index=False), flush=True)
filas = []
for dr in np.arange(-0.03, 0.0201, 0.005):
    filas.append({"Ajuste retorno real anual": dr, **q(M.simular(pros, "META", ordenes_ano=ords, dr=dr, n=10000))})
inv = pd.DataFrame(filas); R["estres_inverso"] = inv; print(inv.round(3).to_string(index=False), flush=True)

# ---------- 4. Asignación táctica (tendencia 10 meses) ----------
px = D.etf_nucleo()[["SPY", "TLH"]].resample("ME").last()
senal = (px.SPY > px.SPY.rolling(10).mean()).shift(1).reindex(K.IDX)      # señal de fin de mes anterior: sin anticipación
nuc = c[["SPY", "TLH", "VCLT"]].reindex(K.IDX); rf_ = 0.5 * nuc.TLH + 0.5 * nuc.VCLT
filas = []
for tilt in [0.0, 0.05, 0.10]:
    t = np.where(senal == True, tilt, -tilt)                               # +tilt a renta variable si hay tendencia, si no a bonos
    t = pd.Series(t, index=K.IDX).fillna(0)
    cambios = (t.diff().abs() > 0).sum(); orden_extra = 3 * cambios / (len(K.IDX) / 12)
    r = p["neto"].reindex(K.IDX) + t * (nuc.SPY - rf_) - COMISION * 3 * (t.diff().abs() > 0) / INV
    m = K.metricas(r.dropna(), K.benchmark(W_A))
    r22t = r.loc["2022"]
    filas.append({"Inclinación táctica": f"±{tilt:.0%}", "Retorno anual": m["Retorno anual"], "Volatilidad": m["Volatilidad"], "Máx. caída": m["Máx. caída"],
                  "TE": m["Tracking error"], "IR": m["Information ratio"], "Sharpe": m["Sharpe"], "Órdenes extra/año": orden_extra,
                  "Meses con señal positiva": senal.mean(), "Retorno 2022": (1 + r22t).prod() - 1})
R["tactica"] = pd.DataFrame(filas); print(R["tactica"].round(4).to_string(index=False))
out = os.path.join(BASE, "resultados", "c_defensa.pkl"); pd.to_pickle(R, out); print(out)
