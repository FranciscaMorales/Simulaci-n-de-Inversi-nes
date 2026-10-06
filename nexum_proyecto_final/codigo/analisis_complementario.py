"""Análisis complementarios (rescatados del trabajo de Francisca y recalculados con el modelo oficial):
contribución al riesgo, Montecarlo con desempleo de Tomás y abanico del patrimonio. Se agregan a resultados/estado.pkl."""
import os
import numpy as np
import pandas as pd
import montecarlo as MC
from config import *

def calcular(S):
    df = S["df"]; W = pd.Series(PESOS_APROBADOS)[ACTIVOS]; Sig = df.cov().values * 12; w = W.values
    mrc = Sig @ w; var = w @ mrc
    rc = pd.DataFrame({"Activo": [NOMBRES[a] for a in ACTIVOS], "Peso": w, "Volatilidad propia": np.sqrt(np.diag(Sig)),
                       "Contribución al riesgo (%)": w * mrc / var, "Contribución a la volatilidad (pp)": w * mrc / np.sqrt(var)})
    real = {a: MC.deflactar(df[a]) for a in ACTIVOS}; fwd = {a: MC.ajustar_media(real[a], CMA[a]) for a in ACTIVOS}
    ph = sum(W[a] * real[a] for a in ACTIVOS); pf = sum(W[a] * fwd[a] for a in ACTIVOS)
    esc = [("Sin desempleo (base)", None),
           ("5% anual, independiente del mercado; reempleo en ~2 años", (0.05, 0.05, -9, 0.5)),
           ("5% normal y 25% si la cartera cayó >10% en 12 meses; reempleo ~2 años", (0.05, 0.25, -0.10, 0.5)),
           ("10% normal y 40% si la cartera cayó >10%; reempleo ~2 años", (0.10, 0.40, -0.10, 0.5)),
           ("Estrés: 6% anual y pérdida PERMANENTE (sin reempleo)", (0.06, 0.06, -9, 0.0))]
    rows = []
    for nombre, d in esc:
        for e_lab, serie in [("Histórico", ph), ("Prospectivo", pf)]:
            r = MC.simular(serie, desempleo=d)
            rows.append({"Escenario de empleo": nombre, "Mercado": e_lab, **{k: r[k] for k in ["P(Educación)", "P(Villarrica)", "P(Herencia)", "P(3 objetivos)"]}})
    ab = {lab: MC.simular(serie, abanico=True)["abanico"] for lab, serie in [("Histórico", ph), ("Prospectivo", pf)]}
    return {"Contribucion_riesgo": rc, "Desempleo": pd.DataFrame(rows),
            "Abanico_historico": ab["Histórico"].assign(Año=range(ANO_HERENCIA + 1)), "Abanico_prospectivo": ab["Prospectivo"].assign(Año=range(ANO_HERENCIA + 1))}

if __name__ == "__main__":
    f = os.path.join(RESULTADOS, "estado.pkl"); S = pd.read_pickle(f)
    S["T"].update(calcular(S)); pd.to_pickle(S, f)
    with pd.ExcelWriter(os.path.join(RESULTADOS, "resultados_modelo.xlsx")) as xw:
        for k, t in S["T"].items(): t.to_excel(xw, sheet_name=k[:31], index=k == "Covarianza_anual")
    pd.set_option("display.width", 220)
    for k in ["Contribucion_riesgo", "Desempleo"]: print(f"\n{k}\n", S["T"][k].round(4).to_string())
    print("\nAbanico prospectivo (años 0,14,20,25,50):\n", S["T"]["Abanico_prospectivo"].iloc[[0, 14, 20, 25, 50]].round(0).to_string())
