"""Palancas de ajuste con las metas en UF (Educación y Villarrica) y la herencia en USD reales. Salida: resultados/palancas_uf.csv"""
import sys, os; sys.path.insert(0, os.getcwd())
import numpy as np, pandas as pd
import datos as D, montecarlo as MC
from config import *
df = pd.read_csv(os.path.join(RESULTADOS, "retornos_mensuales_6_activos.csv"), index_col=0, parse_dates=True)
W = pd.Series(PESOS_APROBADOS)
fxp = D.etf_extra()["CLP=X"]; fxp = fxp[fxp > 100]
fx = np.log(fxp.resample("ME").last()).diff().reindex(df.index); fx_d = fx - fx.mean()
fwd = {a: MC.ajustar_media(MC.deflactar(df[a]), CMA[a]) for a in ACTIVOS}; pn_f = sum(W[a] * fwd[a] for a in ACTIVOS)
rows = []
for lab, vf, hf in [("Plan actual", 1, 1), ("Herencia USD 250 mil", 1, .5), ("Villarrica -25%", .75, 1), ("Ambas", .75, .5)]:
    r = MC.simular(pn_f, fx_d, villarrica_f=vf, herencia_f=hf); rows.append({"Palanca": lab, **{k: v for k, v in r.items() if k.startswith("P(")}})
t = pd.DataFrame(rows); print(t.round(4).to_string(index=False)); t.to_csv(os.path.join(RESULTADOS, "palancas_uf.csv"), index=False)
