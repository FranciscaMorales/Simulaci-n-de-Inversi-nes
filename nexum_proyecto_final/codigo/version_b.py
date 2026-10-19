"""Versión B del informe: la casa de Villarrica forma parte de la herencia.
Herencia financiera = USD 500.000 menos el valor neto de la casa pagada con la cartera (UF 10.500, 5% de costos de venta).
Riesgo de precio calibrado con el IPV de casas usadas del BCCh (deriva 0% real, volatilidad histórica)."""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); os.chdir(os.path.dirname(os.path.abspath(__file__)))
from config import *
import montecarlo as MC, datos as D, objetivos as OB
from objetivos import pagos_educacion, USD_UF
import casa_herencia as CH
COSTO = 0.05; CASA_NETA = VILLARRICA_UF * USD_UF * (1 - COSTO)
HER_FIN = HERENCIA_USD - CASA_NETA
fac_a = OB.factibilidad(); t_a = fac_a["TIR requerida"]
t_b = OB.tir(OB.flujos(herencia=HER_FIN))
cf = OB.flujos(herencia=HER_FIN); ent = np.zeros(len(cf)); ent[0] = CAPITAL * (1 - RESERVA); ent[1:N_APORTES + 1] = APORTE
cob_b = OB.vp(ent, .025) / OB.vp(ent - cf, .025)
S = pickle.load(open("../resultados/estado.pkl", "rb")); df = S["df"]
c = D.mensual(D.etf_nucleo()); x = D.mensual(D.etf_extra()); agf_b = 0.5 * x.AGG + 0.5 * x.BNDX
ar = {"SPY": MC.deflactar(c.SPY), "EFA": MC.deflactar(x.EFA), "BONOS_GLOBAL": MC.deflactar(agf_b)}
ar = {k: v.reindex(df.index) for k, v in ar.items()}
ag_h = sum(AGF[k] * ar[k] for k in AGF); ag_f = sum(AGF[k] * MC.ajustar_media(ar[k].dropna(), CMA[k]).reindex(df.index) for k in AGF)
kw = dict(mu=0.0, sigma=CH.SIG_H, rho=max(CH.RHO_H, 0), costo=COSTO)
rows = []
for cart, h, f in [("Nexum", CH.pn_h, CH.pn_f), ("AGF 85/15", ag_h, ag_f)]:
    for esc, s in [("Histórico 2013-2026", h), ("Prospectivo", f)]:
        for mon, z in [("USD", None), ("UF", CH.fx_d)]:
            a = CH.sim(s, z, con_casa=False); b = CH.sim(s, z, **kw)
            rows.append({"Cartera": cart, "Escenario": esc, "Moneda": mon, "P(3) actual": a["P(3 objetivos)"],
                         "P(Villarrica)": b["P(Villarrica)"], "P(Herencia) B": b["P(Herencia)"], "P(3) B": b["P(3 objetivos)"]})
R = pd.DataFrame(rows)
print(f"Casa neta USD {CASA_NETA:,.0f}; herencia financiera USD {HER_FIN:,.0f}; TIR A {t_a:.4f}  TIR B {t_b:.4f}; cobertura A {fac_a['Cobertura (recursos / objetivos)']:.3f} B {cob_b:.3f}")
print(R.round(3).to_string())
R.to_csv("../resultados/version_b_montecarlo.csv", index=False)
pd.DataFrame([{"TIR A": t_a, "TIR B": t_b, "Cobertura A": fac_a["Cobertura (recursos / objetivos)"], "Cobertura B": cob_b, "Casa neta USD": CASA_NETA, "Herencia financiera USD": HER_FIN}]).to_csv("../resultados/version_b_tir.csv", index=False)
