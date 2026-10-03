"""(1) Verifica los pesos Markowitz de Matías y los somete al mismo walk-forward que
Black-Litterman para medir sobreajuste. (2) Palancas del cliente: efecto de subir
aportes o ajustar la herencia, en el escenario base y en uno de menor retorno."""
import importlib.util
import os

import numpy as np
import pandas as pd
from scipy.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "resultados")


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rep = load("rep", "01_verificacion_replica.py")
ASSETS, df = rep.ASSETS, rep.df


def markowitz(frame):
    mu = frame.mean().values * 12
    S = frame.cov().values * 12
    i = {a: ASSETS.index(a) for a in ASSETS}
    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1},
            {"type": "ineq", "fun": lambda w: w[[0, 1, 2]].sum() - 0.60},
            {"type": "ineq", "fun": lambda w: 0.70 - w[[0, 1, 2]].sum()},
            {"type": "ineq", "fun": lambda w: w[i["TLH"]] - 0.08},
            {"type": "ineq", "fun": lambda w: w[i["VCLT"]] - 0.08},
            {"type": "ineq", "fun": lambda w: w[i["ROT_ACC"]] - 0.05}]
    best = None
    g = np.random.default_rng(777)
    for _ in range(25):
        res = minimize(lambda w: -(w @ mu) / np.sqrt(w @ S @ w), g.dirichlet(np.ones(6)), method="SLSQP",
                       bounds=[(0, 1)] * 6, constraints=cons, options={"maxiter": 2000, "ftol": 1e-14})
        if res.success and (best is None or res.fun < best.fun):
            best = res
    return pd.Series(best.x, index=ASSETS), -best.fun


w_full, sh = markowitz(df)
print("Markowitz muestra completa:", w_full.round(4).to_dict(), "Sharpe", round(sh, 4))


def stats(r):
    idx = (1 + r).cumprod()
    return {"cagr": idx.iloc[-1] ** (12 / len(r)) - 1, "vol": r.std(ddof=1) * np.sqrt(12),
            "mdd": (idx / idx.cummax() - 1).min()}


rets, ws = [], []
for year in range(2018, 2027):
    wy, _ = markowitz(df.loc[: f"{year - 1}-12-31"])
    test = df.loc[f"{year}-01-01": f"{year}-12-31"]
    rets.append(sum(wy[k] * test[k] for k in ASSETS))
    ws.append(wy.rename(year))
wf_mk = pd.concat(rets)
ins_mk = sum(w_full[k] * df.loc[wf_mk.index, k] for k in ASSETS)
tab = pd.DataFrame({"Walk-forward Markowitz": stats(wf_mk), "Markowitz dentro de muestra": stats(ins_mk)}).T
print(tab.round(4).to_string())
print(pd.DataFrame(ws).round(3).to_string())
tab.to_csv(os.path.join(OUT, "walkforward_markowitz.csv"))
pd.DataFrame(ws).to_csv(os.path.join(OUT, "walkforward_markowitz_pesos.csv"))

# ---------------- Palancas del cliente
real = rep.real
cagr_obs = (1 + real).prod() ** (12 / len(real)) - 1


def shifted(target):
    return (1 + real) * ((1 + target) / (1 + cagr_obs)) ** (1 / 12) - 1


def run(series, aporte=10_000.0, herencia=500_000.0):
    old_ap, old_her = rep.APORTE, rep.HER
    rep.APORTE, rep.HER = aporte, herencia
    try:
        return rep.simulate(series)
    finally:
        rep.APORTE, rep.HER = old_ap, old_her


rows = []
for esc, serie in [("Base histórica (6,7% real)", real), ("Retorno menor (5,0% real)", shifted(0.05))]:
    for label, ap, her in [("Plan actual", 10_000, 500_000), ("Aporte USD 12.500/año", 12_500, 500_000),
                           ("Aporte USD 15.000/año", 15_000, 500_000), ("Herencia USD 400.000", 10_000, 400_000),
                           ("Aporte 12.500 y herencia 400.000", 12_500, 400_000)]:
        pe, pv, ph, pj = run(serie, ap, her)
        rows.append({"escenario": esc, "palanca": label, "p_educ": pe, "p_villa": pv, "p_her": ph, "p_conj": pj})
pal = pd.DataFrame(rows)
pal.to_csv(os.path.join(OUT, "palancas_cliente.csv"), index=False)
print(pal.round(4).to_string())
