"""Objetivos del cliente: flujos en USD reales y UF, TIR requerida y factibilidad."""
import numpy as np
import pandas as pd
from scipy.optimize import brentq
from config import *

USD_UF = UF_CLP / USD_CLP

def pagos_educacion():
    pago = ARANCEL_CLP / USD_CLP / ANOS_CARRERA
    p = {}
    for ini in (INICIO_VICENTE, INICIO_EMILIA):
        for y in range(ini, ini + ANOS_CARRERA): p[y] = p.get(y, 0) + pago
    return p

def flujos(n_aportes=N_APORTES, crec_arancel=0.0, aportes_nominales=False, herencia=HERENCIA_USD, villarrica=VILLARRICA_UF, infl=0.025):
    cf = np.zeros(ANO_HERENCIA + 1); cf[0] = CAPITAL
    for t in range(1, n_aportes + 1): cf[t] += APORTE / ((1 + infl) ** t if aportes_nominales else 1)
    for y, v in pagos_educacion().items(): cf[y] -= v * (1 + crec_arancel) ** y
    cf[ANO_VILLARRICA] -= villarrica * USD_UF; cf[ANO_HERENCIA] -= herencia
    return cf

def tir(cf): return brentq(lambda r: sum(v / (1 + r) ** t for t, v in enumerate(cf)), -0.5, 0.5)
def vp(cf, r): return sum(v / (1 + r) ** t for t, v in enumerate(cf))

def tabla_tir():
    esc = [("Base: flujos del enunciado (19 aportes reales)", {}),
           ("14 aportes efectivos (riesgo de empleo)", dict(n_aportes=14)),
           ("Aportes en USD nominales (inflación 2,5%)", dict(aportes_nominales=True)),
           ("Arancel crece 2% real anual", dict(crec_arancel=0.02)),
           ("Aportes nominales + arancel +2% real", dict(aportes_nominales=True, crec_arancel=0.02)),
           ("Lo anterior con 14 aportes", dict(aportes_nominales=True, crec_arancel=0.02, n_aportes=14)),
           ("Palanca: herencia USD 250 mil", dict(herencia=250_000)),
           ("Palanca: Villarrica -25%", dict(villarrica=VILLARRICA_UF * 0.75)),
           ("Palanca: ambas", dict(herencia=250_000, villarrica=VILLARRICA_UF * 0.75))]
    return pd.DataFrame([{"Escenario": n, "TIR real requerida": tir(flujos(**k))} for n, k in esc])

def factibilidad(r_libre=0.025):
    cf = flujos()
    ent = np.zeros(len(cf)); ent[0] = CAPITAL; ent[1:N_APORTES + 1] = APORTE        # entradas brutas
    recursos = vp(ent, r_libre); objetivos = vp(ent - cf, r_libre)                   # salidas brutas = entradas - neto
    t = tir(cf); edu = sum(v / (1 + t) ** y for y, v in pagos_educacion().items())
    vil = VILLARRICA_UF * USD_UF / (1 + t) ** ANO_VILLARRICA; her = HERENCIA_USD / (1 + t) ** ANO_HERENCIA
    tot = edu + vil + her
    return {"Tasa real libre de riesgo": r_libre, "VP recursos (capital + aportes)": recursos, "VP objetivos": objetivos,
            "Cobertura (recursos / objetivos)": recursos / objetivos, "TIR requerida": t,
            "Peso VP Educación": edu / tot, "Peso VP Villarrica": vil / tot, "Peso VP Herencia": her / tot}

def plan_desembolsos():
    rows = [{"Año": y, "Concepto": "Educación", "USD reales": v, "UF": v / USD_UF, "CLP de hoy": v * USD_CLP} for y, v in sorted(pagos_educacion().items())]
    rows += [{"Año": ANO_VILLARRICA, "Concepto": "Villarrica (desembolso; UF 15.000 adicionales vienen de la venta de la casa, fuera de la cartera)",
              "USD reales": VILLARRICA_UF * USD_UF, "UF": VILLARRICA_UF, "CLP de hoy": VILLARRICA_UF * UF_CLP},
             {"Año": ANO_HERENCIA, "Concepto": "Herencia (USD 250 mil por hijo)", "USD reales": HERENCIA_USD, "UF": HERENCIA_USD / USD_UF, "CLP de hoy": HERENCIA_USD * USD_CLP}]
    return pd.DataFrame(rows)

def aversion_riesgo(df_spy_m, rf_m):
    """Parámetro A del inversionista de mercado: A = (E[Rm] - rf) / σm² (Bodie-Kane-Marcus)."""
    ex = (df_spy_m - rf_m).dropna(); return ex.mean() * 12 / (df_spy_m.std() ** 2 * 12)
