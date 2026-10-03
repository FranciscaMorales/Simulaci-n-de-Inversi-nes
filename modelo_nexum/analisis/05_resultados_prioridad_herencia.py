"""Re-corre todos los resultados del informe con el orden de prioridades
educación -> herencia -> Villarrica. Regla del IPS: en el año 25 se aparta una
reserva para la herencia (valor presente de la meta a 25 años, descontado al
retorno real requerido de 4,68%) y la casa se compra solo si el saldo sobre esa
reserva alcanza para pagarla completa; si no, se posterga."""
import importlib.util
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "resultados", "prioridad_herencia")
os.makedirs(OUT, exist_ok=True)
spec = importlib.util.spec_from_file_location("rep", os.path.join(HERE, "01_verificacion_replica.py"))
rep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rep)

ASSETS, df, W = rep.ASSETS, rep.df, pd.Series(rep.w_csv)
EDU, VILLA, HER = rep.EDU, rep.VILLA, rep.HER
R_RESERVA = 0.0468
acwi = pd.read_csv(os.path.join(HERE, "..", "datos", "acwi_mensual.csv"), index_col=0, parse_dates=True)["ACWI"]


def real(nominal, infl=0.02):
    return ((1 + nominal) / (1 + infl) ** (1 / 12) - 1).values


def blend(w, frame):
    return sum(w[k] * frame[k] for k in w.index)


def simulate(series, cap=144_000.0, n_ap=19, aporte=10_000.0, edu_mult=1.0, villa_mult=1.0, her=HER,
             desempleo=None, parcial=False, block=12, n=50_000, seed=777):
    rng = np.random.default_rng(seed)
    paths = np.empty((n, 600))
    for s in range(n):
        paths[s] = rep.mbb(series, 600, block, rng)
    rng_emp = np.random.default_rng(seed + 1)
    villa = VILLA * villa_mult
    bal = np.full(n, float(cap))
    edu_ok = np.ones(n, bool)
    anual = np.empty((n, 51))
    anual[:, 0] = bal
    for m in range(1, 601):
        y = m // 12
        bal = bal * (1 + paths[:, m - 1])
        if m % 12 == 4 and 1 <= y <= n_ap:
            if desempleo is None:
                bal = bal + aporte
            else:
                p_base, p_crisis, umbral = desempleo
                ret12 = np.prod(1 + paths[:, max(0, m - 12):m], axis=1) - 1
                p = np.where(ret12 < umbral, p_crisis, p_base)
                bal = bal + aporte * (rng_emp.random(n) >= p)
        if m % 12 == 0 and y in EDU:
            pago = EDU[y] * edu_mult
            edu_ok &= pago - bal <= 1e-6
            bal = np.maximum(bal - pago, 0)
        if m == 300:
            pre25 = bal.copy()
            disponible = np.maximum(bal - her / (1 + R_RESERVA) ** 25, 0)
            pago = np.minimum(disponible, villa) if parcial else np.where(disponible >= villa - 1e-6, villa, 0.0)
            villa_ok = pago >= villa - 1e-6
            villa_frac = pago / villa
            bal = bal - pago
        if m % 12 == 0:
            anual[:, y] = bal
        if m == 600:
            pre50 = bal.copy()
            her_ok = bal >= her - 1e-6
    return {"p_educ": edu_ok.mean(), "p_villa": villa_ok.mean(), "villa_frac": villa_frac.mean(),
            "p_her": her_ok.mean(), "p_conj": (edu_ok & villa_ok & her_ok).mean(), "anual": anual,
            "pre25": pre25, "pre50": pre50, "her_falta_med": np.median((her - pre50)[~her_ok]) if (~her_ok).any() else 0.0}


def fila(nombre, r, **extra):
    d = {"escenario": nombre, "p_educ": r["p_educ"], "p_villa": r["p_villa"], "villa_financiada": r["villa_frac"],
         "p_her": r["p_her"], "p_conj": r["p_conj"]}
    d.update(extra)
    return d


def guardar(rows, archivo):
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(OUT, archivo), index=False)
    print(f"\n== {archivo}\n", t.round(4).to_string())


base_real = real(blend(W, df))
cagr = (1 + base_real).prod() ** (12 / len(base_real)) - 1


def shifted(target, s=base_real):
    c = (1 + s).prod() ** (12 / len(s)) - 1
    return (1 + s) * ((1 + target) / (1 + c)) ** (1 / 12) - 1


# Base, abanico y faltantes
b = simulate(base_real)
bp = simulate(base_real, parcial=True)
fan = pd.DataFrame({f"p{p}": np.percentile(b["anual"], p, axis=0) for p in (5, 25, 50, 75, 95)})
fan.index.name = "anio"
fan.to_csv(os.path.join(OUT, "abanico.csv"))
print("Base:", {k: round(v, 4) for k, v in b.items() if k.startswith("p_") or k == "villa_frac"})
print("Casa parcial permitida:", {k: round(v, 4) for k, v in bp.items() if k.startswith("p_") or k == "villa_frac"})
print("Faltante mediano herencia cuando falla:", round(b["her_falta_med"]))
print("Percentiles antes del año 25:", np.percentile(b["pre25"], [5, 25, 50, 75, 95]).round(0))
print("Percentiles antes del año 50:", np.percentile(b["pre50"], [5, 25, 50, 75, 95]).round(0))
print("Reserva herencia año 25:", round(HER / (1 + R_RESERVA) ** 25))

# Método
guardar([fila(f"bloques {k}", simulate(base_real, block=k)) for k in (1, 6, 12, 24)]
        + [fila("retorno real 6,5%", simulate(shifted(0.065)))], "metodo.csv")

# Curva probabilidad vs retorno
guardar([fila("curva", simulate(shifted(t)), cagr_real=t)
         for t in [0.035, 0.04, 0.045, 0.05, 0.055, 0.06, 0.065, cagr, 0.07, 0.075, 0.08]], "curva.csv")

# Estrés
nom = blend(W, df)
guardar([
    fila("base", b),
    fila("aportes hasta año 10", simulate(base_real, n_ap=10)),
    fila("shock inicial -30%", simulate(base_real, cap=144_000 * 0.70)),
    fila("inflación 4%", simulate(real(nom, 0.04))),
    fila("peso se aprecia: educación +20% en USD", simulate(base_real, edu_mult=1.2)),
    fila("UF +15% frente al USD", simulate(base_real, villa_mult=1.15)),
    fila("retorno -1pp", simulate(shifted(cagr - 0.01))),
    fila("retorno +1pp", simulate(shifted(cagr + 0.01))),
    fila("desempleo 5%/25%", simulate(base_real, desempleo=(0.05, 0.25, -0.10))),
    fila("desempleo 10%/40%", simulate(base_real, desempleo=(0.10, 0.40, -0.10))),
], "estres.csv")

# Ventanas
n = len(df)
rows = []
for lab, i0, i1 in [("Completa", 0, n), ("Ultimos 10 años", n - 120, n), ("Ultimos 5 años", n - 60, n),
                    ("Primera mitad", 0, n // 2 + 1), ("Segunda mitad", n // 2 + 1, n)]:
    s = real(blend(W, df.iloc[i0:i1]))
    rows.append(fila(lab, simulate(s, block=min(12, len(s) // 2)), meses=len(s),
                     cagr_real=(1 + s).prod() ** (12 / len(s)) - 1))
guardar(rows, "ventanas.csv")

# Alternativas (feb-2013 a ago-2026)
win = df.loc[acwi.index]
W_MK = pd.Series({"SPY": 0.5176583707374599, "TLH": 0.08, "VCLT": 0.08, "MOM_CMD": 0.07519006855835164,
                  "ROT_ACC": 0.05, "LOW_VOL": 0.1971515607041887})
guardar([
    fila("Nexum", simulate(real(blend(W, win)))),
    fila("Markowitz", simulate(real(blend(W_MK, win)))),
    fila("AGF 85/15", simulate(real(0.85 * acwi + 0.075 * win["TLH"] + 0.075 * win["VCLT"]), cap=150_000)),
    fila("60/40 núcleo", simulate(real(0.6 * win["SPY"] + 0.2 * win["TLH"] + 0.2 * win["VCLT"]))),
], "alternativas.csv")

# Palancas
rows = []
for esc, s in [("Base", base_real), ("Prudente 5%", shifted(0.05))]:
    for lab, ap, her in [("Plan actual", 10_000, HER), ("Aporte 12.500", 12_500, HER), ("Aporte 15.000", 15_000, HER),
                         ("Herencia 400.000", 10_000, 400_000), ("Aporte 12.500 y herencia 400.000", 12_500, 400_000)]:
        rows.append(fila(f"{esc} | {lab}", simulate(s, aporte=ap, her=her)))
guardar(rows, "palancas.csv")
