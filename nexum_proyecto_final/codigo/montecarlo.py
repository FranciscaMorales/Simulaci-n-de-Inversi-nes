"""Montecarlo de 50 años (bootstrap mensual) en USD real y en UF, histórico y prospectivo."""
import numpy as np
import pandas as pd
from config import *
from objetivos import pagos_educacion, USD_UF

def deflactar(r): return (1 + r) / (1 + INFLACION_USD) ** (1 / 12) - 1
def ajustar_media(r_real, g):
    l = np.log1p(r_real); return np.expm1(l - l.mean() + np.log1p(g) / 12)

def simular(serie_real, fx=None, n=N_SIMS, seed=SEMILLA, villarrica_f=1.0, herencia_f=1.0, desempleo=None, abanico=False):
    """desempleo = (p_normal, p_crisis, umbral_12m, p_reempleo): cada abril, si Tomás está empleado pierde el trabajo con
    p_normal (o p_crisis si la cartera cayó más que el umbral en 12 meses); si está desempleado no aporta y se reemplea
    con p_reempleo (0 = pérdida permanente). abanico=True devuelve percentiles anuales del patrimonio."""
    """serie_real: retornos mensuales reales de la cartera. fx: Δlog USD/CLP sin tendencia (activa la versión UF)."""
    uf = fx is not None
    s = pd.concat([serie_real, fx if uf else serie_real * 0], axis=1).dropna().values
    rng = np.random.default_rng(seed); bal = np.full(n, CAPITAL * (1 - RESERVA)); rer = np.ones(n)
    edu = pagos_educacion(); ok_e = np.ones(n, bool); ok_v = np.zeros(n, bool); ok_h = np.zeros(n, bool)
    idx = np.ones(n); pk = idx.copy(); mdd = np.zeros(n); s25 = s50 = None
    rng_e = np.random.default_rng(seed + 1); empleado = np.ones(n, bool); r12 = np.ones(n); anual = np.empty((n, ANO_HERENCIA + 1)); anual[:, 0] = bal
    for m in range(1, 601):
        y = m // 12; i = rng.integers(0, len(s), n); bal *= 1 + s[i, 0]; r12 *= 1 + s[i, 0]
        idx *= 1 + s[i, 0]; pk = np.maximum(pk, idx); mdd = np.minimum(mdd, idx / pk - 1)
        if uf: rer *= np.exp(s[i, 1])
        if m % 12 == MES_APORTE and 1 <= y <= N_APORTES:
            if desempleo is not None:
                pn, pc, um, pr = desempleo; u = rng_e.random(n)
                pierde = empleado & (u < np.where(r12 - 1 < um, pc, pn)); vuelve = (~empleado) & (u < pr)
                empleado = (empleado & ~pierde) | vuelve
            bal += APORTE * empleado
        if m % 12 == MES_APORTE: r12 = np.ones(n)
        if m % 12 == 0 and y in edu:
            pago = edu[y] / (rer if uf else 1); ok_e &= bal >= pago - 1e-6; bal = np.maximum(bal - pago, 0)
        if m == ANO_VILLARRICA * 12:
            s25 = bal * (rer if uf else 1); pago = VILLARRICA_UF * USD_UF * villarrica_f / (rer if uf else 1)
            ok_v = bal >= pago - 1e-6; bal = np.maximum(bal - pago, 0)
        if m == ANO_HERENCIA * 12:
            s50 = bal * (rer if uf else 1); ok_h = bal >= HERENCIA_USD * herencia_f - 1e-6
        if abanico and m % 12 == 0: anual[:, y] = (s25 if m == ANO_VILLARRICA * 12 else (s50 if m == ANO_HERENCIA * 12 else bal * (rer if uf else 1)))
    u = USD_UF if uf else 1.0
    return {"P(Educación)": ok_e.mean(), "P(Villarrica)": ok_v.mean(), "P(Herencia)": ok_h.mean(), "P(3 objetivos)": (ok_e & ok_v & ok_h).mean(),
            "Saldo año 25 P10": np.percentile(s25, 10) / u, "Saldo año 25 P50": np.median(s25) / u, "Saldo año 25 P90": np.percentile(s25, 90) / u,
            "Saldo año 50 P10": np.percentile(s50, 10) / u, "Saldo año 50 P50": np.median(s50) / u,
            "Máx. caída mediana": np.median(mdd), "Máx. caída peor 5%": np.percentile(mdd, 5), "Unidad": "UF" if uf else "USD reales",
            **({"abanico": pd.DataFrame(np.percentile(anual, [10, 25, 50, 75, 90], axis=0).T / u, columns=["P10", "P25", "P50", "P75", "P90"])} if abanico else {})}
