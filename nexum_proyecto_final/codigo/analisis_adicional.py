"""Análisis agregados en octubre de 2026 (trabajo de Francisca, sobre el modelo oficial):
  1. Benchmark por clase de activo: backtest 2013-2026 y 2016-2026, atribución del retorno activo y decisión de duración.
  2. Resultado en vivo por clase de activo desde el 14-sep (exports de StockTrak del 6-oct).
  3. Forward USD/CLP firmado el 28-sep-2026: condiciones, pagos al vencimiento y simulación de su efecto.
  4. Reglas de rebalanceo: bandas, regla de commodities y activos adicionales (AGG, EFA).
Lee resultados/estado.pkl (run_all.py) y escribe resultados/analisis_adicional.xlsx y resultados/adicional.pkl, que usa informe.py.
Uso: python3 analisis_adicional.py   (≈1 min).  python3 analisis_adicional.py --desfase agrega el control de calendario del backtest (≈4 min).
"""
import os, sys
import numpy as np
import pandas as pd
import datos as D, estrategias as E, portafolio as PF, montecarlo as MC
from config import *

S = pd.read_pickle(os.path.join(RESULTADOS, "estado.pkl")); df = S["df"]; port = S["port"]; bench = S["bench"]
W = pd.Series(PESOS_APROBADOS)[ACTIVOS]; COMISION_STOCKTRAK = 10.0
c = D.mensual(D.etf_nucleo()); x = D.mensual(D.etf_extra()); bil = c.BIL
T = {}

# ---------------- 1. Benchmark por clase de activo ----------------
MEZCLA_CMD = c[CMD["universo"]].mean(axis=1)
RF_LARGA = 0.5 * c.TLH + 0.5 * c.VCLT          # proxy invertible del Bloomberg U.S. Long Government/Credit (BLV no está en la base)
CLASES = {"Renta variable EE.UU.": (["SPY", "LOW_VOL", "MOM_EQ"], "S&P 500 (SPY)", c.SPY),
          "Renta fija larga EE.UU.": (["TLH", "VCLT"], "Bloomberg U.S. Long Government/Credit (proxy: 50% TLH + 50% VCLT)", RF_LARGA),
          "Commodities": (["MOM_CMD"], "Bloomberg Commodity Index TR (DJP)", x.DJP.reindex(df.index))}
comp = sum(W[a].sum() * b.reindex(df.index) for a, _, b in CLASES.values())
filas, filas_c = [], []
for per, ini in [("2016-2026", INICIO_BENCH), ("2013-2026", INICIO_EVAL)]:
    idx = df.loc[ini:].index
    for clase, (act, nb, b) in CLASES.items():
        w = W[act]; rn = (df[act] * w).sum(axis=1) / w.sum(); rb = b.reindex(df.index)
        mn = PF.metricas(rn.loc[idx], bil, df.SPY, rb.loc[idx]); mb = PF.metricas(rb.loc[idx], bil, df.SPY)
        activo = (rn - rb).loc[idx].mean() * 12
        filas.append({"Período": per, "Clase": clase, "Benchmark": nb, "Peso": w.sum(), "Retorno Nexum": mn["CAGR"], "Retorno benchmark": mb["CAGR"],
                      "Vol. Nexum": mn["Volatilidad"], "Vol. benchmark": mb["Volatilidad"], "Sharpe Nexum": mn["Sharpe"], "Sharpe benchmark": mb["Sharpe"],
                      "Máx. caída Nexum": mn["Máx. caída"], "Máx. caída benchmark": mb["Máx. caída"], "Tracking error": mn["Tracking error"],
                      "Information ratio": mn["Information ratio"], "Retorno activo anual": activo, "Aporte a la cartera (pp)": w.sum() * activo})
    for lab, r in [("Cartera Nexum", port), ("Benchmark de política (por sleeve)", bench), ("Benchmark por clase de activo", comp)]:
        m = PF.metricas(r.loc[idx], bil, df.SPY, comp.loc[idx])
        filas_c.append({"Período": per, "Serie": lab, **{k: m[k] for k in ["CAGR", "Volatilidad", "Sharpe", "Máx. caída", "Beta", "Tracking error", "Information ratio"]}})
T["Benchmark_clases"] = pd.DataFrame(filas); T["Benchmark_compuesto"] = pd.DataFrame(filas_c)
rf_n = (df[["TLH", "VCLT"]] * W[["TLH", "VCLT"]]).sum(axis=1) / W[["TLH", "VCLT"]].sum()
dur = []
for lab, r in [("Renta fija Nexum (TLH + VCLT, duración ~14)", rf_n), ("Bonos EE.UU. amplio (AGG, duración ~6)", x.AGG.reindex(df.index))]:
    m = PF.metricas(r, bil, df.SPY)
    dur.append({"Serie": lab, "Retorno anual": m["CAGR"], "Volatilidad": m["Volatilidad"], "Máx. caída": m["Máx. caída"], "Correlación con S&P 500": r.corr(df.SPY),
                "Feb-mar 2020 (S&P 500 −19%)": (1 + r.loc["2020-02":"2020-03"]).prod() - 1, "2022 (alza de tasas)": (1 + r.loc["2022"]).prod() - 1})
T["Duracion_renta_fija"] = pd.DataFrame(dur)

# ---------------- 2. En vivo por clase de activo (14-sep a 6-oct) ----------------
ST = os.path.join(DATOS, "stocktrak_2026-10-06")
tx = pd.read_csv(os.path.join(ST, "TransactionHistory.csv")); pos = pd.read_csv(os.path.join(ST, "OpenPosition.csv"))
tx["monto"] = tx.Amount.str.replace(r"[\$,]", "", regex=True).astype(float); tx["fecha"] = pd.to_datetime(tx.CreateDate.str[:10])
tx["op"] = tx.TransactionType.str.contains("Buy|Sell")
clase_de = lambda s: "Renta fija larga EE.UU." if s in ("TLH", "VCLT") else "Commodities" if s in ("USO", "CPER") else "Liquidez (reserva)" if s == "SGOV" else "Renta variable EE.UU."
tx["clase"] = tx.Symbol.map(clase_de); pos["clase"] = pos.Symbol.map(clase_de)
compra14 = -tx[(tx.fecha == "2026-09-14") & tx.TransactionType.str.contains("Buy")].groupby("clase").monto.sum()
vivo = pd.DataFrame({"Invertido el 14-sep": compra14, "Flujos": tx.groupby("clase").monto.sum(), "Operaciones": tx[tx.op].groupby("clase").size(),
                     "Valor al 6-oct": pos.groupby("clase").MarketValue.sum()}).fillna(0)
vivo["Resultado (USD)"] = vivo["Valor al 6-oct"] + vivo["Flujos"] - COMISION_STOCKTRAK * vivo["Operaciones"]
vivo["Retorno Nexum"] = vivo["Resultado (USD)"] / vivo["Invertido el 14-sep"]
pv = pd.read_csv(os.path.join(DATOS, "precios_vivo_2026-10-06.csv"), header=[0, 1], index_col=0, parse_dates=True)
entrada = tx[(tx.fecha == "2026-09-14") & tx.TransactionType.str.contains("Buy")].set_index("Symbol").Price.str.replace("$", "").astype(float)
def rt(t):
    """Retorno total desde nuestro precio de entrada del 14-sep (o el cierre de ese día si no compramos el ETF) al 6-oct."""
    tr, ci = pv["retorno_total"][t], pv["cierre"][t]
    return tr.iloc[-1] / tr.loc["2026-09-14"] * ci.loc["2026-09-14"] / entrada.get(t, ci.loc["2026-09-14"]) - 1
bvivo = {"Renta variable EE.UU.": ("S&P 500 (SPY)", rt("SPY")), "Renta fija larga EE.UU.": ("Bloomberg U.S. Long Gov/Credit (proxy TLH/VCLT 50/50)", 0.5 * rt("TLH") + 0.5 * rt("VCLT")),
         "Commodities": ("Mezcla de 5 ETF (DJP sin precios en vivo)", np.mean([rt(t) for t in CMD["universo"]])), "Liquidez (reserva)": ("T-Bills 0-3 meses (SGOV)", rt("SGOV"))}
vivo["Benchmark"] = [bvivo[k][0] for k in vivo.index]; vivo["Retorno benchmark"] = [bvivo[k][1] for k in vivo.index]
vivo["Diferencia (pp)"] = (vivo["Retorno Nexum"] - vivo["Retorno benchmark"]) * 100
orden = ["Renta variable EE.UU.", "Renta fija larga EE.UU.", "Commodities", "Liquidez (reserva)"]
T["Vivo_por_clase"] = vivo.loc[orden].reset_index().rename(columns={"index": "Clase", "clase": "Clase"})
assert abs(vivo["Resultado (USD)"].sum() - (pos.MarketValue.sum() + CAPITAL + tx.monto.sum() - COMISION_STOCKTRAK * tx.op.sum() - CAPITAL)) < 0.01

# ---------------- 3. Forward USD/CLP ----------------
FWD = dict(banco="BDCH", contrato="28-sep-2026", vencimiento="30-sep-2027", monto=104_000.0, spot=967.32, puntos=-4.24, precio=963.08)
VALOR_28SEP = CAPITAL * (1 - 0.0152)            # la cartera acumulaba −1,52% el 28-sep (bitácora)
N, F, S0 = FWD["monto"], FWD["precio"], FWD["spot"]
T["Forward_condiciones"] = pd.DataFrame([
    {"Concepto": "Contraparte", "Valor": FWD["banco"]}, {"Concepto": "Fecha de contrato", "Valor": FWD["contrato"]},
    {"Concepto": "Vencimiento", "Valor": FWD["vencimiento"]}, {"Concepto": "Monto (USD)", "Valor": N},
    {"Concepto": "Tipo de cambio spot (CLP por USD)", "Valor": S0}, {"Concepto": "Puntos forward", "Valor": FWD["puntos"]},
    {"Concepto": "Precio forward (CLP por USD)", "Valor": F}, {"Concepto": "Puntos como % del spot (≈ tasa CLP − tasa USD)", "Valor": F / S0 - 1},
    {"Concepto": "Costo de la cobertura a spot constante (USD)", "Valor": N * (F - S0) / S0},
    {"Concepto": "Cobertura sobre el mandato (USD 150.000)", "Valor": N / CAPITAL}, {"Concepto": "Cobertura sobre el valor al 28-sep", "Valor": N / VALOR_28SEP},
    {"Concepto": "Tipo de cambio que agota la reserva cambiaria de 2% (USD 3.000)", "Valor": F / (1 - 0.02 * CAPITAL / N)}])
T["Forward_escenarios"] = pd.DataFrame([{"Dólar al vencimiento (CLP)": s, "Compensación (MM CLP)": N * (F - s) / 1e6, "Compensación (USD)": N * (F - s) / s,
                                         "Lectura": "Nexum recibe" if s < F else ("—" if s == F else "Nexum paga")} for s in [850, 900, 950, F, 1000, 1050, 1100]])
fxp = D.etf_extra()["CLP=X"]; fxp = fxp[fxp > 100]
dfx = pd.concat([port, np.log(fxp.resample("ME").last()).diff().reindex(port.index)], axis=1, keys=["r", "fx"]).dropna()
rng = np.random.default_rng(SEMILLA); i = rng.integers(0, len(dfx), (N_SIMS, 12))
R = np.prod(1 + dfx.r.values[i], axis=1) - 1; ST_ = S0 * np.exp((dfx.fx.values - dfx.fx.mean())[i].sum(axis=1))   # dólar sin tendencia, vol. y correlación históricas
liq_usd = N * (F - ST_) / ST_
usd_sin = R; usd_con = R + liq_usd / VALOR_28SEP
clp_sin = (1 + R) * ST_ / S0 - 1; clp_con = clp_sin + N * (F - ST_) / (VALOR_28SEP * S0)
pct = lambda a, q: np.percentile(a, q)
T["Forward_simulacion"] = pd.DataFrame([{"Medido en": m, "Cartera": cart, "Retorno medio 12m": a.mean(), "Volatilidad": a.std(), "Peor 5%": pct(a, 5),
                                         "Peor 1%": pct(a, 1), "P(pérdida > 10%)": (a < -0.10).mean()}
                                        for m, cart, a in [("CLP (moneda de las metas)", "Sin cobertura", clp_sin), ("CLP (moneda de las metas)", "Con el forward", clp_con),
                                                           ("USD (moneda funcional)", "Sin cobertura", usd_sin), ("USD (moneda funcional)", "Con el forward", usd_con)]])
peor = usd_sin <= pct(usd_sin, 10)
T["Forward_liquidacion"] = pd.DataFrame([{"Indicador": "Probabilidad de que Nexum pague al vencimiento", "Valor": (liq_usd < 0).mean()},
    {"Indicador": "Probabilidad de pagar más que la reserva cambiaria (USD 3.000)", "Valor": (liq_usd < -0.02 * CAPITAL).mean()},
    {"Indicador": "Pago en el 5% de escenarios más adversos (USD)", "Valor": -pct(liq_usd, 5)},
    {"Indicador": "Cobro en el 5% de escenarios más favorables (USD)", "Valor": pct(liq_usd, 95)},
    {"Indicador": "Compensación media en el 10% de peores años de la cartera en USD", "Valor": liq_usd[peor].mean()},
    {"Indicador": "Volatilidad histórica anual USD/CLP (2013-2026)", "Valor": dfx.fx.std() * np.sqrt(12)},
    {"Indicador": "Correlación cartera Nexum vs. Δ USD/CLP (mensual)", "Valor": dfx.r.corr(dfx.fx)}])
hs = np.round(np.arange(0, 1.21, 0.05), 2)
vol_h = [(clp_sin + h * VALOR_28SEP * (F - ST_) / (VALOR_28SEP * S0)).std() for h in hs]
T["Forward_razon_cobertura"] = pd.DataFrame({"Razón de cobertura": hs, "Volatilidad 12m en CLP": vol_h})

# ---------------- 4. Reglas de rebalanceo ----------------
NUCLEO = ["SPY", "TLH", "VCLT"]; OPS = {"SPY": 1, "TLH": 1, "VCLT": 1, "MOM_CMD": 2, "MOM_EQ": 7, "LOW_VOL": 10}   # órdenes por sleeve al rebalancear
def bandas(bn, bs, calendario=False, nunca=False):
    w = W.copy(); r_, ev, ops, rot = [], 0, 0, 0.0
    for _, r in df.iterrows():
        g = (w * (1 + r)).sum(); r_.append(g - 1); w = w * (1 + r) / g
        lim = pd.Series({a: bn if a in NUCLEO else bs for a in ACTIVOS})
        if not nunca and (calendario or ((w - W).abs() > lim + 1e-12).any()):
            dv = (w - W).abs(); ev += 1; rot += dv.sum() / 2; ops += sum(OPS[a] for a in ACTIVOS if dv[a] * CAPITAL >= 500); w = W.copy()
    s = pd.Series(r_, index=df.index); a = len(df) / 12; m = PF.metricas(s, bil, df.SPY)
    return {"Rebalanceos por año": ev / a, "Órdenes por año": ops / a, "Rotación anual": rot / a, "Retorno anual": m["CAGR"], "Volatilidad": m["Volatilidad"],
            "Desvío vs. pesos fijos (TE)": (s - port).std() * np.sqrt(12)}
T["Bandas_rebalanceo"] = pd.DataFrame([{"Regla": lab, **bandas(**kw)} for lab, kw in [
    ("Mensual por calendario", dict(bn=0, bs=0, calendario=True)), ("Bandas ±3 / ±1 pp", dict(bn=.03, bs=.01)), ("Bandas ±5 / ±2 pp (vigente)", dict(bn=.05, bs=.02)),
    ("Bandas ±7 / ±3 pp", dict(bn=.07, bs=.03)), ("Sin rebalanceo", dict(bn=0, bs=0, nunca=True))]])

def commodities(modo):
    """Mismo motor y filtros que estrategias.momentum_commodities; cambia solo cómo se reparte el sleeve."""
    u = CMD["universo"]; px = D.etf_nucleo()[u + ["BIL"]].loc[:FIN_DATOS]
    me = px.resample("ME").last(); mm = px.rolling(200, min_periods=150).mean().resample("ME").last()
    v12 = px.pct_change().rolling(252, min_periods=180).std().resample("ME").last() * np.sqrt(252)
    r1, r3, r6, r12 = (me.pct_change(k) for k in (1, 3, 6, 12)); fechas = list(me.index[me.index >= CMD["inicio"]]); nq = []
    def sel(t):
        e = pd.DataFrame({"r3": r3.loc[t, u], "r6": r6.loc[t, u], "r12": r12.loc[t, u], "px": me.loc[t, u], "mm": mm.loc[t, u], "v": v12.loc[t, u]}).dropna()
        ok = list(e[(e.r3 > CMD["th_r3"]) & (e.r6 > CMD["th_r6"]) & (e.r12 > CMD["th_r12"]) & (e.px > e.mm) & (e.v < CMD["vol_max"])].index); nq.append(len(ok))
        if modo == "igual": return {k: 1 / len(ok) for k in ok}
        h = {k: (0.2 if modo == "quinto" else min(0.5, 1 / len(ok))) for k in ok}
        if 1 - sum(h.values()) > 1e-9: h["BIL"] = 1 - sum(h.values())
        return h
    out = E._bucle(fechas, sel, r1, r1["BIL"])["retorno"].reindex(df.index)
    return out, pd.Series(nq, index=fechas).loc[INICIO_EVAL:]
filas = []
for modo, lab in [("igual", "Partes iguales entre los que califican (vigente)"), ("quinto", "Cupo fijo de 1/5 por ETF; T-Bills en los cupos sin señal"),
                  ("tope", "Partes iguales con tope de 50% por ETF; resto en T-Bills")]:
    s, nq = commodities(modo)
    if modo == "igual": assert (s - df.MOM_CMD).abs().max() < 1e-12; T["Commodities_califican"] = nq.value_counts().sort_index().rename_axis("ETF que califican").reset_index(name="Meses")
    d_ = df.copy(); d_["MOM_CMD"] = s; p_ = (d_ * W).sum(axis=1); ms = PF.metricas(s, bil, df.SPY); mp = PF.metricas(p_, bil, df.SPY)
    filas.append({"Regla": lab, "Sleeve: retorno anual": ms["CAGR"], "Sleeve: volatilidad": ms["Volatilidad"], "Sleeve: Sharpe": ms["Sharpe"], "Sleeve: máx. caída": ms["Máx. caída"],
                  "Cartera: retorno anual": mp["CAGR"], "Cartera: Sharpe": mp["Sharpe"],
                  "P(3 objetivos) histórico": MC.simular(sum(W[a] * MC.deflactar(d_[a]) for a in ACTIVOS))["P(3 objetivos)"]})
T["Regla_commodities"] = pd.DataFrame(filas)

CMA_EXTRA = {"AGG": 0.024}                   # supuesto propio: entre TLH (2,6%) y bonos globales (2,0%), por su menor duración
d = df.assign(AGG=x.AGG.reindex(df.index), EFA=x.EFA.reindex(df.index)); rf = W["TLH"] + W["VCLT"]
VAR = {"Vigente": dict(W), "Duración intermedia: 50% de la renta fija en AGG": {**W, "TLH": W.TLH / 2, "VCLT": W.VCLT / 2, "AGG": rf / 2},
       "Internacional: 5 pp del S&P 500 a EFA": {**W, "SPY": W.SPY - 0.05, "EFA": 0.05},
       "Ambos cambios": {**W, "TLH": W.TLH / 2, "VCLT": W.VCLT / 2, "AGG": rf / 2, "SPY": W.SPY - 0.05, "EFA": 0.05}}
filas = []
for lab, w in VAR.items():
    w = pd.Series(w); p_ = (d[w.index] * w).sum(axis=1); m = PF.metricas(p_, bil, df.SPY, bench)
    h = sum(w[a] * MC.deflactar(d[a]) for a in w.index); f = sum(w[a] * MC.ajustar_media(MC.deflactar(d[a]), {**CMA, **CMA_EXTRA}[a]) for a in w.index)
    filas.append({"Variante": lab, "Retorno anual": m["CAGR"], "Volatilidad": m["Volatilidad"], "Sharpe": m["Sharpe"], "Máx. caída": m["Máx. caída"],
                  "TE vs. benchmark de política": m["Tracking error"], "P(3 objetivos) histórico": MC.simular(h)["P(3 objetivos)"],
                  "P(3 objetivos) prospectivo": MC.simular(f)["P(3 objetivos)"]})
T["Activos_adicionales"] = pd.DataFrame(filas)

# ---------------- 5. Control de calendario del backtest (opcional) ----------------
if "--desfase" in sys.argv:
    def bucle_t1(fechas, seleccion, r1, bil_r1, guardar=None):
        """Pesos decididos al cierre de t ganan el retorno de t a t+1 (el motor oficial aplica la selección de t al mes t+1 a t+2)."""
        prev, rows = {}, []
        for i, t in enumerate(fechas[:-1]):
            h = seleccion(t); tn = fechas[i + 1]
            fr = r1.loc[tn] if tn in r1.index else pd.Series(dtype=float)
            g = sum(w * (0.0 if pd.isna(fr.get(k, np.nan)) else fr.get(k)) for k, w in h.items()) if h else (bil_r1.get(tn, 0.0) or 0.0)
            rows.append((tn, g - E._costo(prev, h), len(h))); prev = h
        return pd.DataFrame(rows, columns=["fecha", "retorno", "n_posiciones"]).set_index("fecha")
    oficial = E._bucle; E._bucle = bucle_t1
    d1 = PF.tabla_retornos({"MOM_EQ": E.momentum_acciones()["retorno"], "LOW_VOL": E.low_volatility()["retorno"], "MOM_CMD": E.momentum_commodities()["retorno"]})
    E._bucle = oficial
    filas = []
    for lab, dd in [("Motor oficial (selección de t aplicada de t+1 a t+2)", df), ("Selección de t aplicada de t a t+1", d1)]:
        fila = {"Versión": lab}
        for a in ["MOM_EQ", "LOW_VOL", "MOM_CMD"]: fila[f"{NOMBRES[a]} CAGR"] = PF.metricas(dd[a], bil, df.SPY)["CAGR"]
        mp = PF.metricas((dd * W).sum(axis=1), bil, df.SPY); fila.update({"Cartera CAGR": mp["CAGR"], "Cartera Sharpe": mp["Sharpe"],
            "P(3 objetivos) histórico": MC.simular(sum(W[a] * MC.deflactar(dd[a]) for a in ACTIVOS))["P(3 objetivos)"]})
        fila.update({f"BL {a}": v for a, v in PF.black_litterman(dd)["w"].items()}); filas.append(fila)
    T["Control_calendario"] = pd.DataFrame(filas)

with pd.ExcelWriter(os.path.join(RESULTADOS, "analisis_adicional.xlsx")) as xw:
    for k, t in T.items(): t.to_excel(xw, sheet_name=k[:31], index=False)
pd.to_pickle(T, os.path.join(RESULTADOS, "adicional.pkl"))
if __name__ == "__main__":
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    for k, t in T.items(): print(f"\n== {k}\n", t.round(4).to_string(index=False))
