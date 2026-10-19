"""La casa de Villarrica como parte de la herencia, con riesgo de precio inmobiliario.
Usa el Montecarlo oficial (mismas series, semilla y supuestos). La casa se valora en UF al comprarla (año 25)
y su precio real evoluciona hasta el año 50 con deriva mu, volatilidad sigma y correlación rho con la cartera."""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); os.chdir(os.path.dirname(os.path.abspath(__file__)))
from config import *
import montecarlo as MC, datos as D
from objetivos import pagos_educacion, USD_UF
S = pickle.load(open("../resultados/estado.pkl", "rb")); df = S["df"]; W = pd.Series(PESOS_APROBADOS)
real = {a: MC.deflactar(df[a]) for a in ACTIVOS}; fwd = {a: MC.ajustar_media(real[a], CMA[a]) for a in ACTIVOS}
pn_h = sum(W[a] * real[a] for a in ACTIVOS); pn_f = sum(W[a] * fwd[a] for a in ACTIVOS)
fxp = D.etf_extra()["CLP=X"]; fxp = fxp[fxp > 100]; fx = np.log(fxp.resample("ME").last()).diff().reindex(df.index); fx_d = fx - fx.mean()

def sim(serie, fx=None, casa_uf=VILLARRICA_UF, mu=0.0, sigma=0.0, rho=0.0, costo=0.05, shock=0.0, con_casa=True):
    uf = fx is not None; s = pd.concat([serie, fx if uf else serie * 0], axis=1).dropna().values
    rng = np.random.default_rng(SEMILLA); rh = np.random.default_rng(SEMILLA + 99); n = N_SIMS
    bal = np.full(n, CAPITAL * (1 - RESERVA)); rer = np.ones(n); edu = pagos_educacion(); ok_e = np.ones(n, bool); lp = np.zeros(n)
    for m in range(1, 601):
        y = m // 12; i = rng.integers(0, len(s), n); r = s[i, 0]; bal *= 1 + r
        if m > ANO_VILLARRICA * 12: lp += np.log1p(r)
        if uf: rer *= np.exp(s[i, 1])
        if m % 12 == MES_APORTE and 1 <= y <= N_APORTES: bal += APORTE
        if m % 12 == 0 and y in edu:
            p = edu[y] / (rer if uf else 1); ok_e &= bal >= p - 1e-6; bal = np.maximum(bal - p, 0)
        if m == ANO_VILLARRICA * 12:
            p = VILLARRICA_UF * USD_UF / (rer if uf else 1); ok_v = bal >= p - 1e-6; bal = np.maximum(bal - p, 0)
        if m == ANO_HERENCIA * 12:
            T_ = ANO_HERENCIA - ANO_VILLARRICA; zp = (lp - lp.mean()) / lp.std()
            z = rho * zp + np.sqrt(1 - rho ** 2) * rh.standard_normal(n)
            precio = np.exp(mu * T_ - 0.5 * sigma ** 2 * T_ + sigma * np.sqrt(T_) * z) * (1 - shock)
            casa = np.where(ok_v & con_casa, casa_uf * USD_UF * precio * (1 - costo) / (rer if uf else 1), 0)
            ok_h = bal + casa >= HERENCIA_USD - 1e-6
    return {"P(Villarrica)": ok_v.mean(), "P(Herencia)": ok_h.mean(), "P(3 objetivos)": (ok_e & ok_v & ok_h).mean()}

# Calibración con el Índice de Precios de Vivienda del BCCh (casas usadas, UF por m², trimestral 2002-2026)
ipv = pd.read_csv("../datos/ipv_bcch_2002_2026.csv", parse_dates=["fecha"]).set_index("fecha")["ipv_casas_usadas"].dropna()
rq = np.log(ipv).diff().dropna()
MU_H = np.log(ipv.iloc[-1] / ipv.iloc[0]) / ((ipv.index[-1] - ipv.index[0]).days / 365.25)   # deriva real anual (log)
SIG_H = rq.std() * 2                                                                         # volatilidad anual
DD_H = (ipv / ipv.cummax() - 1).min()                                                         # peor caída histórica
cart_q = np.log1p(pn_h).resample("QS").sum()
cart_q.index = cart_q.index + pd.DateOffset(months=2)   # trimestre ene-mar se rotula 1-mar, como el IPV
RHO_H = pd.concat([rq.rename("casa"), cart_q.rename("cart")], axis=1, join="inner").corr().iloc[0, 1]
print(f"IPV casas usadas: deriva real {np.expm1(MU_H):.2%}, vol {SIG_H:.2%}, peor caída {DD_H:.1%}, correlación con la cartera {RHO_H:.2f}")
ESC = [("IPV histórico: deriva y volatilidad 2002-2026", dict(mu=MU_H, sigma=SIG_H, rho=max(RHO_H, 0))),
       ("IPV: deriva 0% real y volatilidad histórica", dict(mu=0.0, sigma=SIG_H, rho=max(RHO_H, 0))),
       ("IPV: deriva 0%, volatilidad histórica y peor caída histórica al vender", dict(mu=0.0, sigma=SIG_H, rho=max(RHO_H, 0), shock=-DD_H)),
("Actual: sin la casa", dict(con_casa=False)),
       ("Casa con valor constante en UF (base)", dict()),
       ("Precio volátil: σ 5% anual", dict(sigma=0.05)),
       ("Precio volátil: σ 10% anual", dict(sigma=0.10)),
       ("σ 10% y correlación 0,5 con la cartera", dict(sigma=0.10, rho=0.5)),
       ("Depreciación real −1% anual, σ 10%, correlación 0,5", dict(mu=-0.01, sigma=0.10, rho=0.5)),
       ("Caída permanente de 30% al vender", dict(shock=0.30)),
       ("Caída de 30% + costos de venta de 10%", dict(shock=0.30, costo=0.10))]
rows = []
for mon, z in [("USD", None), ("UF", fx_d)]:
    for lab, kw in ESC: rows.append({"Moneda": mon, "Escenario (prospectivo)": lab, **sim(pn_f, z, **kw)})
R = pd.DataFrame(rows); print(R.round(3).to_string())
corte = [{"Caída del precio de la casa": c, "P(3 objetivos)": sim(pn_f, None, shock=c)["P(3 objetivos)"]} for c in [0, .2, .4, .6, .8, 1.0]]
C = pd.DataFrame(corte); print(C.round(3).to_string())
R.to_csv("../resultados/casa_herencia.csv", index=False); C.to_csv("../resultados/casa_herencia_caidas.csv", index=False)
