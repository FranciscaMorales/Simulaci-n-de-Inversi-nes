"""Efecto de priorizar la herencia sobre Villarrica: en el año 25 la casa solo se
compra si, después de pagarla, queda una reserva suficiente para la herencia
(valor presente de USD 500.000 a 25 años, descontado a una tasa real prudente)."""
import importlib.util, os
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("rep", os.path.join(HERE, "01_verificacion_replica.py"))
rep = importlib.util.module_from_spec(spec); spec.loader.exec_module(rep)


def sim(series, tasa_reserva=None, parcial=False, n=50_000, seed=777):
    rng = np.random.default_rng(seed)
    paths = np.empty((n, 600))
    for s in range(n):
        paths[s] = rep.mbb(series, 600, 12, rng)
    bal = np.full(n, 144_000.0); edu = np.ones(n, bool)
    for m in range(1, 601):
        y = m // 12
        bal = bal * (1 + paths[:, m - 1])
        if m % 12 == 4 and 1 <= y <= 19:
            bal += 10_000
        if m % 12 == 0 and y in rep.EDU:
            edu &= rep.EDU[y] - bal <= 1e-6
            bal = np.maximum(bal - rep.EDU[y], 0)
        if m == 300:
            reserva = 0.0 if tasa_reserva is None else rep.HER / (1 + tasa_reserva) ** 25
            disponible = np.maximum(bal - reserva, 0)
            pago = np.minimum(disponible, rep.VILLA) if parcial else np.where(disponible >= rep.VILLA, rep.VILLA, 0.0)
            villa_ok = pago >= rep.VILLA - 1e-6
            villa_frac = pago / rep.VILLA
            bal = bal - pago
        if m == 600:
            her_ok = bal >= rep.HER - 1e-6
    return edu.mean(), villa_ok.mean(), villa_frac.mean(), her_ok.mean(), (edu & villa_ok & her_ok).mean()


cagr = (1 + rep.real).prod() ** (12 / len(rep.real)) - 1
prud = (1 + rep.real) * ((1.05) / (1 + cagr)) ** (1 / 12) - 1
rows = []
for esc, s in [("Base historica 6,7% real", rep.real), ("Prudente 5% real", prud)]:
    for lab, r, parc in [("Villarrica antes que herencia (actual)", None, False),
                         ("Herencia primero, reserva al 4,7% (todo o nada)", 0.0468, False),
                         ("Herencia primero, reserva al 4,7% (casa parcial)", 0.0468, True),
                         ("Herencia primero, reserva al 3,0% (todo o nada)", 0.03, False)]:
        e, v, vf, h, j = sim(s, r, parc)
        rows.append({"escenario": esc, "regla": lab, "p_educ": e, "p_villa_completa": v,
                     "pct_casa_financiada_prom": vf, "p_herencia": h, "p_las_tres": j})
df = pd.DataFrame(rows)
df.to_csv(os.path.join(HERE, "..", "resultados", "prioridad_herencia.csv"), index=False)
print(df.round(4).to_string())
print("Reserva a 4,7%:", round(rep.HER / 1.0468 ** 25), " a 3%:", round(rep.HER / 1.03 ** 25))
