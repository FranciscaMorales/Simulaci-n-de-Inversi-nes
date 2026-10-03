"""Replica independiente de BlackLitterman_Nexum.py y Simulacion_Montecarlo.py
(carpeta NEXUM_FINAL_AUDITADO de Matías) para verificar que las cifras del informe
coinciden con el modelo. Misma ventana, mismos supuestos, misma semilla (777)."""
import os

import numpy as np
import pandas as pd
from scipy.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "datos", "common_window_final.csv")
OUT = os.path.join(HERE, "..", "resultados")
ASSETS = ["SPY", "TLH", "VCLT", "MOM_CMD", "ROT_ACC", "LOW_VOL"]
DELTA, TAU = 2.5, 0.05

df = pd.read_csv(DATA, index_col=0, parse_dates=True)[ASSETS]
S = df.cov().values * 12

vols = np.sqrt(np.diag(S))
w_ref = (1 / vols) / (1 / vols).sum()
rc_ref = w_ref * (S @ w_ref) / (w_ref @ S @ w_ref)
pi = DELTA * S @ w_ref

P = np.zeros((2, 6))
P[0, ASSETS.index("SPY")] = 1.0
P[1, ASSETS.index("LOW_VOL")] = 1.0
P[1, ASSETS.index("MOM_CMD")] = -1.0
Q = np.array([0.06, 0.02])
Omega = np.diag(np.diag(P @ (TAU * S) @ P.T))
A = np.linalg.inv(TAU * S) + P.T @ np.linalg.inv(Omega) @ P
b = np.linalg.inv(TAU * S) @ pi + P.T @ np.linalg.inv(Omega) @ Q
mu_bl = np.linalg.solve(A, b)

core = [0, 1, 2]
cons = [{"type": "eq", "fun": lambda w: w.sum() - 1},
        {"type": "ineq", "fun": lambda w: w[core].sum() - 0.60},
        {"type": "ineq", "fun": lambda w: 0.70 - w[core].sum()}]
best = None
rng = np.random.default_rng(777)
for _ in range(25):
    res = minimize(lambda w: -(w @ mu_bl) / np.sqrt(w @ S @ w), rng.dirichlet(np.ones(6)),
                   method="SLSQP", bounds=[(0, 1)] * 6, constraints=cons,
                   options={"maxiter": 2000, "ftol": 1e-14})
    if res.success and (best is None or res.fun < best.fun):
        best = res
w_bl = best.x

bl = pd.DataFrame({"vol_anual": vols, "w_ref_inv_vol": w_ref, "rc_ref": rc_ref, "pi": pi,
                   "mu_BL": mu_bl, "peso_BL": w_bl}, index=ASSETS)
print("=== Black-Litterman replicado ===")
print(bl.round(5))
print(f"Sharpe (mu_BL/vol): {-best.fun:.4f}   nucleo: {w_bl[core].sum():.4%}")
bl.to_csv(os.path.join(OUT, "replica_BL.csv"))

# ---------------- Montecarlo: replica exacta de la logica de Matias ----------------
INFL = 0.02
MINF = (1 + INFL) ** (1 / 12) - 1
CAP0 = 150_000 * 0.96
APORTE, N_AP = 10_000.0, 19
VILLA, HER = 470_385.0751834344, 500_000.0
EDU = {14: 14_257.981727848033, 15: 14_257.981727848033, 16: 28_515.963455696066,
       17: 28_515.963455696066, 18: 28_515.963455696066, 19: 14_257.981727848033,
       20: 14_257.981727848033}

w_csv = dict(zip(ASSETS, [0.3739659775260731, 0.15887249959159544, 0.13798996447032344,
                          0.11649183713906823, 0.0853867447366308, 0.1272929765363091]))
blend = sum(w_csv[k] * df[k] for k in ASSETS)
real = ((1 + blend) / (1 + MINF) - 1).values


def mbb(series, n_months, block, rng):
    n = len(series)
    out = np.empty(n_months)
    filled = 0
    while filled < n_months:
        start = rng.integers(0, n - block + 1) if block < n else 0
        blk = series[start:start + block]
        take = min(block, n_months - filled)
        out[filled:filled + take] = blk[:take]
        filled += take
    return out


def simulate(series, n_sims=50_000, block=12, seed=777, cap=CAP0, n_aportes=N_AP):
    rng = np.random.default_rng(seed)
    paths = np.empty((n_sims, 600))
    for s in range(n_sims):
        paths[s] = mbb(series, 600, block, rng)
    bal = np.full(n_sims, cap)
    educ_ok = np.ones(n_sims, bool)
    villa_ok = her_ok = None
    for m in range(1, 601):
        y = m // 12
        bal = bal * (1 + paths[:, m - 1])
        if m % 12 == 4 and 1 <= y <= n_aportes:
            bal = bal + APORTE
        if m % 12 == 0 and y in EDU:
            educ_ok &= (np.maximum(EDU[y] - bal, 0) <= 1e-6)
            bal = np.maximum(bal - EDU[y], 0)
        if m == 300:
            villa_ok = np.maximum(VILLA - bal, 0) <= 1e-6
            bal = np.maximum(bal - VILLA, 0)
        if m == 600:
            her_ok = np.maximum(HER - bal, 0) <= 1e-6
            bal = np.maximum(bal - HER, 0)
    joint = educ_ok & villa_ok & her_ok
    return educ_ok.mean(), villa_ok.mean(), her_ok.mean(), joint.mean()


if __name__ == "__main__":
    cagr = (1 + real).prod() ** (12 / len(real)) - 1
    vol = real.std(ddof=1) * np.sqrt(12)
    print(f"\nCAGR real cartera {cagr:.4%}  vol {vol:.4%}")
    pe, pv, ph, pj = simulate(real)
    print(f"MC base replicado: P(Educ)={pe:.4%} P(Villa)={pv:.4%} P(Her)={ph:.4%} P(conj)={pj:.4%}")
    print("Matias reporta:    P(Educ)=100.00% P(Villa)=96.402% P(Her)=90.002% P(conj)=90.002%")
