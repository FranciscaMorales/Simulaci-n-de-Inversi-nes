"""Compara la cartera real de StockTrak (14, 21 y 30 de septiembre de 2026) con el modelo
auditado de la carpeta NEXUM_FINAL_AUDITADO: pesos Black-Litterman por sleeve, señal de la
regla de commodities, stop-loss sugeridos y efecto de los pesos ejecutados en el Monte Carlo
(regla educación -> herencia -> casa del informe)."""
import importlib.util
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
OUT = os.path.join(HERE, "..", "resultados", "implementacion")
os.makedirs(OUT, exist_ok=True)
spec = importlib.util.spec_from_file_location("rep", os.path.join(HERE, "01_verificacion_replica.py"))
rep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rep)

ASSETS, df, S = rep.ASSETS, rep.df, rep.S
BL = pd.Series(rep.w_csv)
MU_BL = pd.Series(rep.mu_bl, index=ASSETS)
# Pesos que usó el PDF "Inversiones" (órdenes del 14-sep) y los del respaldo previo a la auditoría
PDF = pd.Series({"SPY": 0.3789, "TLH": 0.1687, "VCLT": 0.1460, "MOM_CMD": 0.0611, "ROT_ACC": 0.0706, "LOW_VOL": 0.1746})
PRE = pd.Series({"SPY": 0.3840590110214573, "TLH": 0.1660133857652136, "VCLT": 0.1310410018646344,
                 "MOM_CMD": 0.09174176823543531, "ROT_ACC": 0.08370639566832251, "LOW_VOL": 0.1434384372859078})
SLEEVE = {"SPY": "SPY", "TLH": "TLH", "VCLT": "VCLT", "SGOV": "RESERVA", "USO": "MOM_CMD", "CPER": "MOM_CMD",
          **{t: "ROT_ACC" for t in ["DELL", "MRNA", "HPE", "VLO", "CNC", "MPC", "STT", "TGT", "EXPD", "BK", "NUE", "SNA"]},
          **{t: "LOW_VOL" for t in ["BRK/B", "ATO", "REG", "DUK", "L", "O", "MCD", "KO", "LIN", "JNJ",
                                    "AFL", "FRT", "PG", "RSG"]}}
# Stop-loss sugerido en el PDF "Inversiones" (precio del 14-sep menos 2 x ATR 14)
STOP = {"DELL": 473.29, "MRNA": 123.83, "HPE": 49.14, "VLO": 355.57, "CNC": 64.46, "MPC": 366.19, "STT": 182.90,
        "TGT": 151.90, "EXPD": 186.28, "BK": 154.73, "BRK/B": 504.17, "ATO": 159.67, "REG": 72.48, "DUK": 115.76,
        "L": 105.78, "O": 57.93, "MCD": 249.63, "KO": 86.48, "LIN": 450.36, "JNJ": 257.00, "USO": 145.61}

snaps = {}
for d in ["2026-09-14", "2026-09-21", "2026-09-30"]:
    s = pd.read_csv(os.path.join(ROOT, "stocktrak", f"{d}.csv"))
    s["sleeve"] = s["Symbol"].map(SLEEVE)
    s["costo"] = s["Quantity"] * s["PricePaid"]
    snaps[d] = s


def motor(serie):
    """Pesos de los 6 sleeves sobre el capital invertido, sin la reserva en SGOV."""
    x = serie.drop("RESERVA")
    return (x / x.sum()).reindex(ASSETS)


# 1. Pesos: modelo vs ejecución
costo = snaps["2026-09-14"].groupby("sleeve")["costo"].sum()
mercado = {d: s.groupby("sleeve")["MarketValue"].sum() for d, s in snaps.items()}
pesos = pd.DataFrame({"BL auditado": BL, "PDF Inversiones": PDF, "BL pre-auditoria": PRE,
                      "Ejecutado 14-sep (costo, % de 144.000)": costo.reindex(ASSETS) / 144_000,
                      **{f"Mercado {d[5:]} (% motor)": motor(m) for d, m in mercado.items()}})
pesos.loc["Nucleo"] = pesos.loc[["SPY", "TLH", "VCLT"]].sum()
pesos.to_csv(os.path.join(OUT, "pesos_por_sleeve.csv"))
print("== Pesos por sleeve (%)\n", (pesos * 100).round(2).to_string())
print(f"Capital de los 144.000 que quedó sin invertir el 14-sep: USD {144_000 - costo.drop('RESERVA').sum():,.0f}")

m30 = mercado["2026-09-30"]
total30 = m30.drop("RESERVA").sum()
ajuste = pd.DataFrame({"valor_30sep": m30.reindex(ASSETS), "objetivo_BL": BL * total30,
                       "comprar(+)/vender(-)": BL * total30 - m30.reindex(ASSETS)})
ajuste.to_csv(os.path.join(OUT, "rebalanceo_a_BL_30sep.csv"))
print(f"\n== Rebalanceo al BL auditado sobre el motor del 30-sep (USD {total30:,.0f})\n", ajuste.round(0).to_string())

# 2. Riesgo y retorno esperado (mu_BL) de cada juego de pesos; TE solo por desvío de asignación
filas = []
for nombre, w in [("BL auditado", BL), ("PDF Inversiones", PDF), ("Ejecutado 14-sep", motor(costo)),
                  ("Mercado 30-sep", motor(m30))]:
    w = w.reindex(ASSETS).values
    dlt = w - BL.values
    filas.append({"pesos": nombre, "mu_BL": w @ MU_BL.values, "vol": np.sqrt(w @ S @ w),
                  "mu_BL/vol": w @ MU_BL.values / np.sqrt(w @ S @ w), "TE_por_asignacion": np.sqrt(dlt @ S @ dlt)})
riesgo = pd.DataFrame(filas)
riesgo.to_csv(os.path.join(OUT, "riesgo_por_pesos.csv"), index=False)
print("\n== Retorno esperado BL, volatilidad y TE por desvío de pesos\n", riesgo.round(4).to_string(index=False))

# 3. Regla de commodities del modelo (GLD/USO/DBA; señal al cierre de mes)
px = pd.read_parquet(os.path.join(HERE, "..", "datos", "core_etf_prices.parquet"))[["GLD", "USO", "DBA"]]
fin = px.resample("ME").last()
mm200 = px.rolling(200, min_periods=150).mean().resample("ME").last()
vol12 = px.pct_change().rolling(252, min_periods=180).std().resample("ME").last() * np.sqrt(252)
senal = []
for t in pd.to_datetime(["2026-07-31", "2026-08-31"]):
    x = pd.DataFrame({"precio": fin.loc[t], "mm200": mm200.loc[t], "r3m": fin.pct_change(3).loc[t],
                      "r6m": fin.pct_change(6).loc[t], "r12m": fin.pct_change(12).loc[t], "vol12m": vol12.loc[t]})
    x["elegible"] = (x.r3m > 0.05) & (x.r6m > 0.08) & (x.r12m > 0.10) & (x.precio > x.mm200) & (x.vol12m < 0.50)
    senal.append(x.assign(senal=t.date()))
senal = pd.concat(senal)
senal.to_csv(os.path.join(OUT, "senal_commodities.csv"))
print("\n== Señal de commodities con la regla del modelo (último dato:", px.index.max().date(), ")\n",
      senal.round(4).to_string())

# 4. Posiciones que siguen en cartera bajo su stop-loss sugerido
for d, s in snaps.items():
    bajo = s[s["Symbol"].map(STOP).gt(s["LastPrice"])]
    print(f"{d}: bajo stop y en cartera ->", list(zip(bajo["Symbol"], bajo["LastPrice"], bajo["Symbol"].map(STOP))))

# 5. Monte Carlo con la regla del informe (reserva de herencia en el año 25, casa solo con excedente)
R_RESERVA = 0.0468


def simulate(series, cap=144_000.0, n=50_000, block=12, seed=777):
    rng = np.random.default_rng(seed)
    paths = np.empty((n, 600))
    for i in range(n):
        paths[i] = rep.mbb(series, 600, block, rng)
    bal = np.full(n, cap)
    edu_ok = np.ones(n, bool)
    for m in range(1, 601):
        y = m // 12
        bal = bal * (1 + paths[:, m - 1])
        if m % 12 == 4 and 1 <= y <= 19:
            bal = bal + 10_000.0
        if m % 12 == 0 and y in rep.EDU:
            edu_ok &= rep.EDU[y] - bal <= 1e-6
            bal = np.maximum(bal - rep.EDU[y], 0)
        if m == 300:
            libre = np.maximum(bal - rep.HER / (1 + R_RESERVA) ** 25, 0)
            casa_ok = libre >= rep.VILLA - 1e-6
            bal = bal - np.where(casa_ok, rep.VILLA, 0.0)
    her_ok = bal >= rep.HER - 1e-6
    return edu_ok.mean(), her_ok.mean(), casa_ok.mean(), (edu_ok & her_ok & casa_ok).mean()


filas = []
for nombre, w in [("BL auditado", BL), ("Ejecutado 14-sep", motor(costo)), ("Mercado 30-sep", motor(m30))]:
    serie = ((1 + sum(w[k] * df[k] for k in ASSETS)) / (1 + rep.MINF) - 1).values
    pe, ph, pc, p3 = simulate(serie)
    filas.append({"pesos": nombre, "cagr_real_historico": (1 + serie).prod() ** (12 / len(serie)) - 1,
                  "p_educacion": pe, "p_herencia": ph, "p_casa": pc, "p_tres": p3})
mc = pd.DataFrame(filas)
mc.to_csv(os.path.join(OUT, "montecarlo_pesos_ejecutados.csv"), index=False)
print("\n== Monte Carlo (50.000 simulaciones, bloques de 12 meses)\n", mc.round(4).to_string(index=False))
