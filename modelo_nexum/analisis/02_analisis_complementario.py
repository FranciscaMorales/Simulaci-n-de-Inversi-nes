"""Análisis complementarios sobre el modelo auditado de Matías (mismo motor de
Montecarlo, misma semilla, mismos supuestos). Cubre lo que la retroalimentación
pidió y el modelo no reportaba: retorno requerido, distribución del patrimonio,
comparación con la cartera 85/15 de la AGF, validación walk-forward de la
asignación, riesgo de desempleo correlacionado y métricas de riesgo ex-ante."""
import os

import numpy as np
import pandas as pd
from scipy.optimize import brentq, minimize

import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "resultados")
spec = importlib.util.spec_from_file_location("rep", os.path.join(HERE, "01_verificacion_replica.py"))
rep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rep)

ASSETS = rep.ASSETS
df = rep.df
W_BL = pd.Series(rep.w_csv)
W_MK = pd.Series({"SPY": 0.5176583707374599, "TLH": 0.08, "VCLT": 0.08, "MOM_CMD": 0.07519006855835164,
                  "ROT_ACC": 0.05, "LOW_VOL": 0.1971515607041887})
acwi = pd.read_csv(os.path.join(HERE, "..", "datos", "acwi_mensual.csv"), index_col=0, parse_dates=True)["ACWI"]
MINF = rep.MINF
EDU, VILLA, HER = rep.EDU, rep.VILLA, rep.HER


def to_real(x):
    return (1 + x) / (1 + MINF) - 1


def stats(r):
    r = pd.Series(r)
    n = len(r)
    idx = (1 + r).cumprod()
    dd = idx / idx.cummax() - 1
    roll12 = (1 + r).rolling(12).apply(np.prod, raw=True) - 1
    q = r.quantile(0.05)
    return {"cagr": idx.iloc[-1] ** (12 / n) - 1, "vol": r.std(ddof=1) * np.sqrt(12),
            "mdd": dd.min(), "peor_12m": roll12.min(), "var95_m": -q, "es95_m": -r[r <= q].mean(),
            "sortino_ratio": (r.mean() * 12) / (r[r < 0].std(ddof=1) * np.sqrt(12))}


# ---------------------------------------------------------------- A. Factibilidad
def flujos(cap):
    f = {0: cap}
    for m in range(1, 601):
        y = m // 12
        if m % 12 == 4 and 1 <= y <= 19:
            f[m] = f.get(m, 0) + 10_000
        if m % 12 == 0 and y in EDU:
            f[m] = f.get(m, 0) - EDU[y]
        if m == 300:
            f[m] = f.get(m, 0) - VILLA
        if m == 600:
            f[m] = f.get(m, 0) - HER
    return f


def npv(rate_annual, f):
    rm = (1 + rate_annual) ** (1 / 12) - 1
    return sum(v / (1 + rm) ** m for m, v in f.items())


fact = []
for cap in (144_000, 150_000):
    irr = brentq(lambda r: npv(r, flujos(cap)), -0.05, 0.30)
    fact.append({"capital": cap, "retorno_real_requerido": irr})
pv_rows = []
for r in (0.02, 0.03, 0.04, 0.05, 0.0669):
    rm = (1 + r) ** (1 / 12) - 1
    pv_edu = sum(v / (1 + rm) ** (12 * y) for y, v in EDU.items())
    pv_vil = VILLA / (1 + rm) ** 300
    pv_her = HER / (1 + rm) ** 600
    pv_ap = sum(10_000 / (1 + rm) ** (12 * y + 4) for y in range(1, 20))
    pv_rows.append({"tasa_real": r, "VP_educacion": pv_edu, "VP_villarrica": pv_vil, "VP_herencia": pv_her,
                    "VP_objetivos": pv_edu + pv_vil + pv_her, "VP_aportes": pv_ap,
                    "VP_recursos": 144_000 + pv_ap,
                    "ratio_cobertura": (144_000 + pv_ap) / (pv_edu + pv_vil + pv_her)})
pd.DataFrame(fact).to_csv(os.path.join(OUT, "factibilidad_retorno_requerido.csv"), index=False)
pd.DataFrame(pv_rows).to_csv(os.path.join(OUT, "factibilidad_valor_presente.csv"), index=False)
print("A. Retorno real requerido:", pd.DataFrame(fact).round(5).to_dict("records"))
print(pd.DataFrame(pv_rows).round(0).to_string())


# ---------------------------------------------------------------- B. Motor MC extendido
def simulate(series, n_sims=50_000, block=12, seed=777, cap=144_000, n_aportes=19,
             desempleo=None, edu=EDU, villa=VILLA):
    rng = np.random.default_rng(seed)
    paths = np.empty((n_sims, 600))
    for s in range(n_sims):
        paths[s] = rep.mbb(series, 600, block, rng)
    rng_emp = np.random.default_rng(seed + 1)
    bal = np.full(n_sims, float(cap))
    educ_ok = np.ones(n_sims, bool)
    anual = np.empty((n_sims, 51))
    anual[:, 0] = bal
    bal_pre25 = bal_pre50 = None
    falta_vil = falta_her = None
    for m in range(1, 601):
        y = m // 12
        bal = bal * (1 + paths[:, m - 1])
        if m % 12 == 4 and 1 <= y <= n_aportes:
            if desempleo is None:
                bal = bal + 10_000
            else:
                p_base, p_crisis, umbral = desempleo
                ret12 = np.prod(1 + paths[:, max(0, m - 12):m], axis=1) - 1
                p = np.where(ret12 < umbral, p_crisis, p_base)
                bal = bal + 10_000 * (rng_emp.random(n_sims) >= p)
        if m % 12 == 0 and y in edu:
            educ_ok &= (edu[y] - bal <= 1e-6)
            bal = np.maximum(bal - edu[y], 0)
        if m == 300:
            bal_pre25 = bal.copy()
            falta_vil = np.maximum(villa - bal, 0)
            bal = np.maximum(bal - villa, 0)
        if m == 600:
            bal_pre50 = bal.copy()
            falta_her = np.maximum(HER - bal, 0)
            bal = np.maximum(bal - HER, 0)
        if m % 12 == 0:
            anual[:, y] = bal if m not in (300, 600) else (bal_pre25 if m == 300 else bal_pre50)
    vil_ok, her_ok = falta_vil <= 1e-6, falta_her <= 1e-6
    return {"p_educ": educ_ok.mean(), "p_villa": vil_ok.mean(), "p_her": her_ok.mean(),
            "p_conj": (educ_ok & vil_ok & her_ok).mean(), "anual": anual,
            "falta_vil_med": np.median(falta_vil[~vil_ok]) if (~vil_ok).any() else 0.0,
            "falta_her_med": np.median(falta_her[~her_ok]) if (~her_ok).any() else 0.0,
            "pre25": bal_pre25, "pre50": bal_pre50}


def blend(w, frame):
    return sum(w[k] * frame[k] for k in w.index)


real_bl = to_real(blend(W_BL, df)).values
base = simulate(real_bl)
pcts = [5, 25, 50, 75, 95]
fan = pd.DataFrame({f"p{p}": np.percentile(base["anual"], p, axis=0) for p in pcts})
fan.index.name = "anio"
fan.to_csv(os.path.join(OUT, "mc_abanico_patrimonio_real.csv"))
print("\nB. Base:", {k: round(v, 5) for k, v in base.items() if k.startswith("p_")})
print("Faltante mediano cuando falla: Villarrica", round(base["falta_vil_med"]), "Herencia", round(base["falta_her_med"]))
print(fan.loc[[0, 5, 10, 13, 20, 24, 25, 30, 40, 49, 50]].round(0).to_string())
print("Percentiles patrimonio antes de Villarrica (año 25):", np.percentile(base["pre25"], pcts).round(0))
print("Percentiles patrimonio antes de herencia (año 50):", np.percentile(base["pre50"], pcts).round(0))

curve = []
cagr_obs = (1 + real_bl).prod() ** (12 / len(real_bl)) - 1
for target in [0.035, 0.04, 0.045, 0.05, 0.055, 0.06, 0.065, cagr_obs, 0.07, 0.075, 0.08]:
    f = ((1 + target) / (1 + cagr_obs)) ** (1 / 12)
    s = (1 + real_bl) * f - 1
    r = simulate(s)
    curve.append({"cagr_real": target, "p_educ": r["p_educ"], "p_villa": r["p_villa"], "p_her": r["p_her"],
                  "p_conj": r["p_conj"]})
curve = pd.DataFrame(curve)
curve.to_csv(os.path.join(OUT, "mc_probabilidad_vs_retorno.csv"), index=False)
print("\nCurva P vs CAGR real:\n", curve.round(4).to_string())

# ---------------------------------------------------------------- C. Desempleo correlacionado (capital humano)
emp_rows = []
for label, d in [("Sin desempleo (base)", None), ("5% anual, independiente del mercado", (0.05, 0.05, -1.0)),
                 ("5% normal, 25% si la cartera cayó >10% en 12m", (0.05, 0.25, -0.10)),
                 ("10% normal, 40% si la cartera cayó >10% en 12m", (0.10, 0.40, -0.10))]:
    r = simulate(real_bl, desempleo=d)
    emp_rows.append({"escenario": label, "p_educ": r["p_educ"], "p_villa": r["p_villa"], "p_her": r["p_her"],
                     "p_conj": r["p_conj"]})
emp = pd.DataFrame(emp_rows)
emp.to_csv(os.path.join(OUT, "mc_desempleo_correlacionado.csv"), index=False)
print("\nC. Desempleo:\n", emp.round(4).to_string())

# ---------------------------------------------------------------- D. Alternativas, ventana común feb-2013 a ago-2026
win = df.loc[acwi.index]
alts = {
    "Nexum (Black-Litterman)": (blend(W_BL, win), 144_000),
    "Markowitz histórico": (blend(W_MK, win), 144_000),
    "AGF actual 85/15 (85% ACWI, 15% TLH/VCLT)": (0.85 * acwi + 0.075 * win["TLH"] + 0.075 * win["VCLT"], 150_000),
    "60/40 núcleo (60% SPY, 20% TLH, 20% VCLT)": (0.6 * win["SPY"] + 0.2 * win["TLH"] + 0.2 * win["VCLT"], 144_000),
}
alt_rows = []
for name, (nom, cap) in alts.items():
    st = stats(nom)
    rr = to_real(nom).values
    sim = simulate(rr, cap=cap)
    alt_rows.append({"cartera": name, "capital": cap, "cagr_nominal": st["cagr"],
                     "cagr_real": (1 + rr).prod() ** (12 / len(rr)) - 1, "vol": st["vol"], "mdd": st["mdd"],
                     "peor_12m": st["peor_12m"], "es95_mensual": st["es95_m"], "p_educ": sim["p_educ"],
                     "p_villa": sim["p_villa"], "p_her": sim["p_her"], "p_conj": sim["p_conj"],
                     "p5_pre_villarrica": np.percentile(sim["pre25"], 5),
                     "p5_anio13": np.percentile(sim["anual"][:, 13], 5)})
alt = pd.DataFrame(alt_rows)
alt.to_csv(os.path.join(OUT, "comparacion_alternativas.csv"), index=False)
print("\nD. Alternativas (163 meses):\n", alt.round(4).to_string())

# ---------------------------------------------------------------- E. Riesgo ex-ante cartera Nexum (164 meses)
nom_bl = blend(W_BL, df)
st = stats(nom_bl)
S = df.cov().values * 12
w = W_BL[ASSETS].values
rc = w * (S @ w) / (w @ S @ w)
corr = df.corr()
idx = (1 + nom_bl).cumprod()
dd = idx / idx.cummax() - 1
trough = dd.idxmin()
peak = idx.loc[:trough].idxmax()
rec = idx.loc[trough:][idx.loc[trough:] >= idx.loc[peak]]
recovery = rec.index[0] if len(rec) else None
mu_m, sd_m = nom_bl.mean(), nom_bl.std(ddof=1)
riesgo = {"cagr_nominal": st["cagr"], "vol_anual": st["vol"], "mdd": st["mdd"], "mdd_pico": str(peak.date()),
          "mdd_valle": str(trough.date()), "mdd_recuperacion": str(recovery.date()) if recovery is not None else "",
          "peor_12m": st["peor_12m"], "var95_mensual_hist": st["var95_m"], "es95_mensual_hist": st["es95_m"],
          "var95_mensual_param": -(mu_m - 1.645 * sd_m), "var95_anual_param": -(mu_m * 12 - 1.645 * sd_m * np.sqrt(12)),
          "sortino_ratio": st["sortino_ratio"], "ret_vol": nom_bl.mean() * 12 / st["vol"],
          "sharpe_rf_1.7": (nom_bl.mean() * 12 - 0.017) / st["vol"],
          "mu_BL_cartera": float(w @ rep.mu_bl), "beta_vs_SPY": np.cov(nom_bl, df["SPY"])[0, 1] / df["SPY"].var()}
pd.Series(riesgo).to_csv(os.path.join(OUT, "riesgo_cartera_nexum.csv"))
pd.DataFrame({"peso": w, "contribucion_riesgo": rc}, index=ASSETS).to_csv(os.path.join(OUT, "contribucion_riesgo.csv"))
corr.to_csv(os.path.join(OUT, "correlaciones.csv"))
print("\nE. Riesgo Nexum:", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in riesgo.items()})
print("Contribución al riesgo:", dict(zip(ASSETS, rc.round(4))))
print(corr.round(2).to_string())

strat = {k: stats(df[k]) for k in ASSETS}
pd.DataFrame(strat).T.to_csv(os.path.join(OUT, "estadisticas_activos_ventana_comun.csv"))
print(pd.DataFrame(strat).T.round(4).to_string())
act = df["ROT_ACC"] - df["SPY"]
print("ROT_ACC vs SPY: retorno activo", round(act.mean() * 12, 4), "TE", round(act.std() * np.sqrt(12), 4))


# ---------------------------------------------------------------- F. Walk-forward de la asignación BL
def bl_weights(frame):
    S_ = frame.cov().values * 12
    v = np.sqrt(np.diag(S_))
    wr = (1 / v) / (1 / v).sum()
    pi = rep.DELTA * S_ @ wr
    Om = np.diag(np.diag(rep.P @ (rep.TAU * S_) @ rep.P.T))
    A = np.linalg.inv(rep.TAU * S_) + rep.P.T @ np.linalg.inv(Om) @ rep.P
    b = np.linalg.inv(rep.TAU * S_) @ pi + rep.P.T @ np.linalg.inv(Om) @ rep.Q
    mu = np.linalg.solve(A, b)
    best = None
    g = np.random.default_rng(777)
    for _ in range(25):
        res = minimize(lambda x: -(x @ mu) / np.sqrt(x @ S_ @ x), g.dirichlet(np.ones(6)), method="SLSQP",
                       bounds=[(0, 1)] * 6, constraints=rep.cons, options={"maxiter": 2000, "ftol": 1e-14})
        if res.success and (best is None or res.fun < best.fun):
            best = res
    return pd.Series(best.x, index=ASSETS)


wf_rets, wf_w = [], []
for year in range(2018, 2027):
    train = df.loc[: f"{year - 1}-12-31"]
    wy = bl_weights(train)
    test = df.loc[f"{year}-01-01": f"{year}-12-31"]
    wf_rets.append(blend(wy, test))
    wf_w.append(wy.rename(year))
wf = pd.concat(wf_rets)
wf_w = pd.DataFrame(wf_w)
oos = df.loc[wf.index]
comp = {"Walk-forward BL (re-estimado cada enero)": wf,
        "Pesos BL finales (dentro de muestra)": blend(W_BL, oos),
        "AGF 85/15 proxy": 0.85 * acwi.loc[wf.index] + 0.075 * oos["TLH"] + 0.075 * oos["VCLT"]}
wf_tab = pd.DataFrame({k: stats(v) for k, v in comp.items()}).T
wf_tab.to_csv(os.path.join(OUT, "walkforward_resultados.csv"))
wf_w.to_csv(os.path.join(OUT, "walkforward_pesos.csv"))
print("\nF. Walk-forward 2018-01 a 2026-08:\n", wf_tab.round(4).to_string())
print(wf_w.round(3).to_string())

half = df.loc[:"2019-12-31"]
w_half = bl_weights(half)
test2 = df.loc["2020-01-01":]
print("\nPesos estimados solo con 2013-2019:", w_half.round(4).to_dict())
print("Fuera de muestra 2020-2026, pesos 2013-2019:", {k: round(v, 4) for k, v in stats(blend(w_half, test2)).items()})
print("Fuera de muestra 2020-2026, pesos finales:", {k: round(v, 4) for k, v in stats(blend(W_BL, test2)).items()})
pd.DataFrame({"pesos_2013_2019": w_half, "pesos_finales": W_BL[ASSETS]}).to_csv(os.path.join(OUT, "oos_mitades_pesos.csv"))
