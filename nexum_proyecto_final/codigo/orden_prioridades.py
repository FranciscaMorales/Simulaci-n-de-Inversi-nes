import os
"""Compara el orden oficial (Educación -> Villarrica -> Herencia) con Educación -> Herencia -> Villarrica,
usando exactamente el Montecarlo oficial (mismas series, semilla y supuestos)."""
import sys, os, pickle, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from config import *
import montecarlo as MC
from objetivos import pagos_educacion, USD_UF
S = pickle.load(open("../resultados/estado.pkl", "rb")); df = S["df"]; T = S["T"]
TIR = float(S["fac"]["TIR requerida"]) if "fac" in S else 0.0465
W = pd.Series(PESOS_APROBADOS)
real = {a: MC.deflactar(df[a]) for a in ACTIVOS}; fwd = {a: MC.ajustar_media(real[a], CMA[a]) for a in ACTIVOS}
pn_h = sum(W[a] * real[a] for a in ACTIVOS); pn_f = sum(W[a] * fwd[a] for a in ACTIVOS)
import datos as D
fxp = D.etf_extra()["CLP=X"]; fxp = fxp[fxp > 100]
fx = np.log(fxp.resample("ME").last()).diff().reindex(df.index); fx_d = fx - fx.mean()

def sim(serie, fx=None, regla="oficial", n=N_SIMS, seed=SEMILLA, tasa=TIR):
    uf = fx is not None
    s = pd.concat([serie, fx if uf else serie * 0], axis=1).dropna().values
    rng = np.random.default_rng(seed); bal = np.full(n, CAPITAL * (1 - RESERVA)); rer = np.ones(n)
    edu = pagos_educacion(); ok_e = np.ones(n, bool)
    for m in range(1, 601):
        y = m // 12; i = rng.integers(0, len(s), n); bal *= 1 + s[i, 0]
        if uf: rer *= np.exp(s[i, 1])
        if m % 12 == MES_APORTE and 1 <= y <= N_APORTES: bal += APORTE
        if m % 12 == 0 and y in edu:
            pago = edu[y] / (rer if uf else 1); ok_e &= bal >= pago - 1e-6; bal = np.maximum(bal - pago, 0)
        if m == ANO_VILLARRICA * 12:
            pago = VILLARRICA_UF * USD_UF / (rer if uf else 1)
            if regla == "oficial":
                ok_v = bal >= pago - 1e-6; bal = np.maximum(bal - pago, 0)
            else:  # herencia primero: se aparta su valor presente y la casa se compra solo con lo que sobra
                reserva = HERENCIA_USD / (1 + tasa) ** (ANO_HERENCIA - ANO_VILLARRICA)
                ok_v = bal - reserva >= pago - 1e-6; bal = np.where(ok_v, bal - pago, bal)
        if m == ANO_HERENCIA * 12: ok_h = bal >= HERENCIA_USD - 1e-6
    return {"P(Educación)": ok_e.mean(), "P(Villarrica)": ok_v.mean(), "P(Herencia)": ok_h.mean(), "P(3 objetivos)": (ok_e & ok_v & ok_h).mean()}

rows = []
for esc, s in [("Histórico", pn_h), ("Prospectivo", pn_f)]:
    for mon, z in [("USD", None), ("UF", fx_d)]:
        for regla, lab in [("oficial", "Educación → Villarrica → Herencia"), ("herencia", "Educación → Herencia → Villarrica")]:
            rows.append({"Escenario": esc, "Moneda": mon, "Orden": lab, **sim(s, z, regla)})
R = pd.DataFrame(rows); pd.set_option("display.width", 200)
print("TIR usada para la reserva:", TIR, " reserva USD:", round(HERENCIA_USD / (1 + TIR) ** 25))
print(R.round(3).to_string())
ofi = T["Montecarlo"]; print(ofi[ofi.Cartera == "Nexum"][["Escenario", "Moneda", "P(Villarrica)", "P(Herencia)", "P(3 objetivos)"]].round(3).to_string())
R.to_csv("../resultados/orden_prioridades.csv", index=False)
