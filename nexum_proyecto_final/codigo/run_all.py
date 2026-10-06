"""Corre el proyecto completo y guarda resultados en /resultados. Uso: python3 run_all.py"""
import json, os
import numpy as np
import pandas as pd
import datos as D, estrategias as E, portafolio as PF, objetivos as O, montecarlo as MC, validacion as V
from config import *

os.makedirs(RESULTADOS, exist_ok=True)
T = {}                                                         # tablas para el Excel de resultados
log = lambda *a: print(*a, flush=True)

# 1. Estrategias (versión corregida)
log("1. Backtests")
mom, lv, cmd = E.momentum_acciones()["retorno"], E.low_volatility()["retorno"], E.momentum_commodities()["retorno"]
df = PF.tabla_retornos({"MOM_EQ": mom, "LOW_VOL": lv, "MOM_CMD": cmd})
c = D.mensual(D.etf_nucleo()); x = D.mensual(D.etf_extra()); bil = c.BIL
df.to_csv(os.path.join(RESULTADOS, "retornos_mensuales_6_activos.csv"))

# 2. Impacto de las correcciones respecto del modelo original
log("2. Impacto de correcciones")
M0 = os.path.expanduser("~/Desktop/Modelo_Final_Nexum/")
old = {k: pd.read_csv(M0 + f, index_col=0, parse_dates=True)["retorno_neto_mensual"] for k, f in
       [("MOM_CMD", "mom_cmd_monthly_returns.csv"), ("MOM_EQ", "momentum_monthly_returns.csv"), ("LOW_VOL", "lowvol_monthly_returns.csv")]}
mom1m = E.momentum_acciones(vol_sharpe="1m")["retorno"]
E.CONVENCION_COSTO_UN_LADO = False
mom2, lv2, cmd2 = E.momentum_acciones()["retorno"], E.low_volatility()["retorno"], E.momentum_commodities()["retorno"]
E.CONVENCION_COSTO_UN_LADO = True
versiones = [("Modelo original (162 meses, vol. 1 mes)", PF.tabla_retornos(old)),
             ("+ incluye jul y dic 2018 (dato faltante corregido)", PF.tabla_retornos({"MOM_EQ": mom1m, "LOW_VOL": lv, "MOM_CMD": cmd})),
             ("+ filtro de Sharpe con vol. 12 meses (versión vigente)", df),
             ("Sensibilidad: costos en ambos lados", PF.tabla_retornos({"MOM_EQ": mom2, "LOW_VOL": lv2, "MOM_CMD": cmd2}))]
imp = []
for lab, d in versiones:
    bl = PF.black_litterman(d); pa = (d * pd.Series(PESOS_APROBADOS)).sum(axis=1); m = PF.metricas(pa, bil, d.SPY)
    imp.append({"Versión": lab, "Meses": len(d), "CAGR Momentum": (1 + d.MOM_EQ).prod() ** (12 / len(d)) - 1,
                "CAGR Low-Vol": (1 + d.LOW_VOL).prod() ** (12 / len(d)) - 1, "CAGR Commodities": (1 + d.MOM_CMD).prod() ** (12 / len(d)) - 1,
                "Cartera (pesos aprobados) CAGR": m["CAGR"], "Cartera Sharpe": m["Sharpe"], "Cartera máx. caída": m["Máx. caída"],
                **{f"BL {a}": bl["w"][a] for a in ACTIVOS}})
T["Impacto_correcciones"] = pd.DataFrame(imp)

# 3. Asignación estratégica
log("3. Markowitz y Black-Litterman")
mk, bl = PF.markowitz(df), PF.black_litterman(df)
W = pd.Series(PESOS_APROBADOS)
T["Asignacion"] = pd.DataFrame({"Activo": [NOMBRES[a] for a in ACTIVOS], "Prior paridad de riesgo": bl["w_eq"].values, "π implícito": bl["pi"].values,
                                "μ Black-Litterman": bl["mu_bl"].values, "Pesos BL recalibrados": bl["w"].values,
                                "Pesos aprobados (en implementación)": W.values, "Diferencia (pp)": (bl["w"].values - W.values) * 100,
                                "Markowitz histórico": mk["w"].values, "Retorno hist. anual": mk["mu"].values,
                                "Volatilidad anual": np.sqrt(np.diag(mk["S"].values))})
T["Covarianza_anual"] = bl["S"]

# 4. Benchmark y métricas
log("4. Benchmark y métricas")
port = (df * W).sum(axis=1); bser = PF.benchmark_series(df.index); bench = (bser * W).sum(axis=1)
agf_bonos = 0.5 * x.AGG + 0.5 * x.BNDX
agf = (AGF["SPY"] * c.SPY + AGF["EFA"] * x.EFA + AGF["BONOS_GLOBAL"] * agf_bonos).reindex(df.index)
w16 = df.loc[INICIO_BENCH:].index
met = []
for per, idx in [("2016-2026", w16), ("2013-2026", df.index)]:
    for lab, r in [("Cartera Nexum", port), ("Benchmark de política", bench), ("Cartera actual AGF 85/15", agf), ("S&P 500 (SPY)", df.SPY)]:
        if per == "2013-2026" and lab == "Benchmark de política": continue
        met.append({"Período": per, "Serie": lab, **PF.metricas(r.loc[idx], bil, df.SPY, bench.loc[w16] if per == "2016-2026" else None)})
T["Metricas"] = pd.DataFrame(met)
act = (port - bench).loc[w16]
sleeve_te = {a: ((df[a] - bser[a]).loc[w16].std() * np.sqrt(12)) for a in ACTIVOS}
T["Tracking_error"] = pd.DataFrame([{"Concepto": "TE ex-ante, pesos aprobados (2016-2026)", "Valor": act.std() * np.sqrt(12)},
    {"Concepto": "TE últimos 36 meses", "Valor": act.iloc[-36:].std() * np.sqrt(12)},
    {"Concepto": "Alfa objetivo anual", "Valor": ALFA_OBJETIVO}, {"Concepto": "Information ratio objetivo", "Valor": IR_OBJETIVO},
    {"Concepto": "TE objetivo = alfa / IR", "Valor": ALFA_OBJETIVO / IR_OBJETIVO}, {"Concepto": "TE máximo (alfa 2% / IR 0,5)", "Valor": TE_MAX}]
    + [{"Concepto": f"TE del sleeve {NOMBRES[a]} vs su benchmark", "Valor": v} for a, v in sleeve_te.items()])
pd.DataFrame({"Cartera": port, "Benchmark": bench, "AGF": agf, "SPY": df.SPY}).to_csv(os.path.join(RESULTADOS, "retornos_cartera_benchmark.csv"))

# 5. Estrategias individuales
est = []
for a, b in [("MOM_EQ", "QMOM"), ("LOW_VOL", "SPLV"), ("MOM_CMD", "MEZCLA_CMD")]:
    est.append({"Estrategia": NOMBRES[a], "Benchmark": b, **PF.metricas(df[a].loc[w16], bil, df.SPY, bser[a].loc[w16])})
    est.append({"Estrategia": NOMBRES[a] + " (2013-2026)", "Benchmark": "—", **PF.metricas(df[a], bil, df.SPY)})
T["Estrategias"] = pd.DataFrame(est)

# 6. Objetivos y TIR
log("6. Objetivos")
T["TIR"] = O.tabla_tir(); fac = O.factibilidad(); T["Factibilidad"] = pd.DataFrame([fac]).T.reset_index().rename(columns={"index": "Concepto", 0: "Valor"})
T["Plan_desembolsos"] = O.plan_desembolsos()
A_mkt = O.aversion_riesgo(df.SPY, bil)
# A implícito del cliente: el que hace óptima (1 fondo) la cartera BL: w* = μ/(A σ²) -> A = μ_p/σ_p² con μ en exceso
mu_p = float(bl["mu_bl"] @ W); var_p = float(W @ bl["S"].values @ W)
T["Aversion_riesgo"] = pd.DataFrame([{"Concepto": "A del inversionista de mercado (S&P 500, 2013-2026)", "Valor": A_mkt},
                                     {"Concepto": "A implícito de la cartera BL (μ_BL / σ²)", "Valor": mu_p / var_p},
                                     {"Concepto": "δ usado en Black-Litterman", "Valor": BL_DELTA}])

# 7. Montecarlo
log("7. Montecarlo")
fxp = D.etf_extra()["CLP=X"]; fxp = fxp[fxp > 100]                # descarta ticks erróneos de Yahoo (p.ej. 5,0)
fx = np.log(fxp.resample("ME").last()).diff().reindex(df.index); fx_d = fx - fx.mean()
real = {a: MC.deflactar(df[a]) for a in ACTIVOS}; fwd = {a: MC.ajustar_media(real[a], CMA[a]) for a in ACTIVOS}
pn_h = sum(W[a] * real[a] for a in ACTIVOS); pn_f = sum(W[a] * fwd[a] for a in ACTIVOS)
ar = {"SPY": MC.deflactar(c.SPY), "EFA": MC.deflactar(x.EFA), "BONOS_GLOBAL": MC.deflactar(agf_bonos)}
ar = {k: v.reindex(df.index) for k, v in ar.items()}
ag_h = sum(AGF[k] * ar[k] for k in AGF); ag_f = sum(AGF[k] * MC.ajustar_media(ar[k].dropna(), CMA[k]).reindex(df.index) for k in AGF)
mc = []
for cart, h, f in [("Nexum", pn_h, pn_f), ("AGF 85/15", ag_h, ag_f)]:
    for esc, s in [("Histórico 2013-2026", h), ("Prospectivo", f)]:
        for mon, z in [("USD", None), ("UF", fx_d)]:
            r = MC.simular(s, z); g = (1 + s.dropna()).prod() ** (12 / len(s.dropna())) - 1
            mc.append({"Cartera": cart, "Escenario": esc, "Moneda": mon, "Retorno real anual": g, **r}); log("  ", cart, esc, mon, round(r["P(3 objetivos)"], 3))
T["Montecarlo"] = pd.DataFrame(mc)
pal = []
for lab, vf, hf in [("Base", 1, 1), ("Herencia USD 250 mil", 1, .5), ("Villarrica -25%", .75, 1), ("Ambas", .75, .5)]:
    pal.append({"Palanca (prospectivo, USD)": lab, **{k: v for k, v in MC.simular(pn_f, None, villarrica_f=vf, herencia_f=hf).items() if k.startswith("P(")}})
T["Palancas"] = pd.DataFrame(pal)
T["Supuestos_mercado"] = pd.DataFrame([{"Activo": k, "Retorno real anual supuesto": v} for k, v in CMA.items()])

# 8. Riesgo cambiario
spy = df.SPY; worst = spy <= spy.quantile(.10); clp = (1 + port) * np.exp(fx) - 1
T["Riesgo_cambiario"] = pd.DataFrame([{"Indicador": "Volatilidad anual USD/CLP", "Valor": fx.std() * np.sqrt(12)},
    {"Indicador": "Correlación S&P 500 vs. Δ USD/CLP", "Valor": spy.corr(fx)},
    {"Indicador": "Δ USD/CLP promedio en el 10% de peores meses del S&P 500", "Valor": fx[worst].mean()},
    {"Indicador": "Retorno cartera en USD (peores meses)", "Valor": port[worst].mean()},
    {"Indicador": "Retorno cartera en CLP (peores meses)", "Valor": clp[worst].mean()},
    {"Indicador": "Volatilidad cartera en USD", "Valor": port.std() * np.sqrt(12)},
    {"Indicador": "Volatilidad cartera en CLP", "Valor": clp.std() * np.sqrt(12)}])

# 9. Validación
log("9. Validación")
rob_f = os.path.join(RESULTADOS, "robustez.csv")
T["Robustez"] = pd.read_csv(rob_f) if os.path.exists(rob_f) else V.robustez(); T["Robustez"].to_csv(rob_f, index=False); T["Walk_forward"] = V.walk_forward(df, bil)


# 10. Sensibilidad al universo de commodities (control del sesgo de selección)
c3 = E.momentum_commodities(universo=CMD["universo_original"])["retorno"]
sens = []
for lab, serie in [("5 ETF (vigente: GLD, USO, DBA, SLV, CPER)", df.MOM_CMD), ("3 ETF (original: GLD, USO, DBA)", c3.reindex(df.index))]:
    d_ = df.copy(); d_["MOM_CMD"] = serie; p_ = (d_ * W).sum(axis=1); m_ = PF.metricas(p_, bil, d_.SPY)
    mc_ = MC.simular(sum(W[a] * MC.deflactar(d_[a]) for a in ACTIVOS))
    sens.append({"Universo": lab, "Cartera CAGR": m_["CAGR"], "Cartera Sharpe": m_["Sharpe"], "Cartera máx. caída": m_["Máx. caída"],
                 "P(3 objetivos) histórico": mc_["P(3 objetivos)"], "Peso BL recalibrado commodities": PF.black_litterman(d_)["w"]["MOM_CMD"]})
T["Sensibilidad_commodities"] = pd.DataFrame(sens)

with pd.ExcelWriter(os.path.join(RESULTADOS, "resultados_modelo.xlsx")) as xw:
    for k, t in T.items(): t.to_excel(xw, sheet_name=k[:31], index=k == "Covarianza_anual")
pd.to_pickle({"T": T, "df": df, "bl": bl, "mk": mk, "bench": bench, "bser": bser, "port": port, "agf": agf, "fac": fac}, os.path.join(RESULTADOS, "estado.pkl"))
log("LISTO")
