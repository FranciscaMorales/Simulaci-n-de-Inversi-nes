"""Palanca/supuesto: Tomás queda sin trabajo y no hay aporte durante 1 o 2 años, en distintos momentos del plan.
Usa exactamente el Montecarlo oficial (mismas series, semilla y supuestos); solo se eliminan los aportes de esos años.
Salida: resultados/desempleo_aportes.csv"""
import sys, os, pickle, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from config import *
import montecarlo as MC
from objetivos import pagos_educacion, USD_UF, flujos, tir
S = pickle.load(open("../resultados/estado.pkl", "rb")); df = S["df"]
W = pd.Series(PESOS_APROBADOS)
real = {a: MC.deflactar(df[a]) for a in ACTIVOS}; fwd = {a: MC.ajustar_media(real[a], CMA[a]) for a in ACTIVOS}
pn_h = sum(W[a] * real[a] for a in ACTIVOS); pn_f = sum(W[a] * fwd[a] for a in ACTIVOS)
import datos as D
fxp = D.etf_extra()["CLP=X"]; fxp = fxp[fxp > 100]
fx = np.log(fxp.resample("ME").last()).diff().reindex(df.index); fx_d = fx - fx.mean()

def sim(serie, fx=None, sin_aporte=(), n=N_SIMS, seed=SEMILLA):
    uf = fx is not None
    s = pd.concat([serie, fx if uf else serie * 0], axis=1).dropna().values
    rng = np.random.default_rng(seed); bal = np.full(n, CAPITAL * (1 - RESERVA)); rer = np.ones(n)
    edu = pagos_educacion(); ok_e = np.ones(n, bool)
    for m in range(1, 601):
        y = m // 12; i = rng.integers(0, len(s), n); bal *= 1 + s[i, 0]
        if uf: rer *= np.exp(s[i, 1])
        if m % 12 == MES_APORTE and 1 <= y <= N_APORTES and y not in sin_aporte: bal += APORTE
        if m % 12 == 0 and y in edu:
            pago = edu[y] / (rer if uf else 1); ok_e &= bal >= pago - 1e-6; bal = np.maximum(bal - pago, 0)
        if m == ANO_VILLARRICA * 12:
            pago = VILLARRICA_UF * USD_UF / (rer if uf else 1); ok_v = bal >= pago - 1e-6; bal = np.maximum(bal - pago, 0)
        if m == ANO_HERENCIA * 12: ok_h = bal >= HERENCIA_USD - 1e-6
    return {"P(Educación)": ok_e.mean(), "P(Villarrica)": ok_v.mean(), "P(Herencia)": ok_h.mean(), "P(3 objetivos)": (ok_e & ok_v & ok_h).mean()}

def tir_sin(sin):
    cf = flujos()
    for y in sin: cf[y] -= APORTE
    return tir(cf)

ESC = [("Base: los 19 aportes", ()),
       ("1 año sin aporte, ahora (año 1)", (1,)), ("2 años sin aporte, ahora (años 1-2)", (1, 2)),
       ("1 año sin aporte, a mitad de camino (año 7)", (7,)), ("2 años sin aporte, a mitad de camino (años 7-8)", (7, 8)),
       ("1 año sin aporte, antes de la universidad (año 13)", (13,)), ("2 años sin aporte, antes de la universidad (años 12-13)", (12, 13)),
       ("2 años sin aporte, con las dos carreras (años 16-17)", (16, 17)),
       ("Palanca combinada: 2 años sin aporte (1-2) + herencia USD 250 mil", "palanca")]
rows = []
for nombre, sin in ESC:
    for e_lab, serie in [("Histórico", pn_h), ("Prospectivo", pn_f)]:
        for mon, f in [("USD", None), ("UF", fx_d)]:
            if sin == "palanca":
                H0 = HERENCIA_USD; globals()["HERENCIA_USD"] = H0 / 2
                r = sim(serie, f, (1, 2)); globals()["HERENCIA_USD"] = H0
                cf = flujos(herencia=H0 / 2); cf[1] -= APORTE; cf[2] -= APORTE; t = tir(cf)
            else:
                r = sim(serie, f, sin); t = tir_sin(sin)
            rows.append({"Escenario": nombre, "Mercado": e_lab, "Moneda": mon, "TIR requerida": t, **r})
R = pd.DataFrame(rows); R.to_csv("../resultados/desempleo_aportes.csv", index=False)
pd.set_option("display.width", 200)
print(R.assign(**{c: (R[c] * 100).round(1) for c in R.columns if c.startswith("P(") or c == "TIR requerida"}).to_string(index=False))
