"""TIR requerida y factibilidad sobre el capital invertido (USD 144.000, neto de la reserva de 4%), como el Montecarlo.
Decisión del grupo con el profesor guía (oct-2026): la reserva no financia metas y así el requerimiento es más exigente.
Actualiza solo las tablas de objetivos en resultados/estado.pkl, sin rehacer backtests ni Montecarlo.
Uso: python3 tir_capital_invertido.py   (después: excel_modelo.py, figuras.py, informe.py)"""
import os
import pandas as pd
import objetivos as O
from config import RESULTADOS

f = os.path.join(RESULTADOS, "estado.pkl"); S = pd.read_pickle(f); T = S["T"]
T["TIR"] = O.tabla_tir(); fac = O.factibilidad(); S["fac"] = fac
T["Factibilidad"] = pd.DataFrame([fac]).T.reset_index().rename(columns={"index": "Concepto", 0: "Valor"})
pd.to_pickle(S, f)
with pd.ExcelWriter(os.path.join(RESULTADOS, "resultados_modelo.xlsx")) as xw:
    for k, t in T.items(): t.to_excel(xw, sheet_name=k[:31], index=k == "Covarianza_anual")
if __name__ == "__main__":
    print(T["TIR"].round(4).to_string(index=False)); print(T["Factibilidad"].round(4).to_string(index=False))
