"""Backtests point-in-time de las tres estrategias activas (señal al cierre de t, retorno en t+1).

Portado del modelo original (Backtesting_Momentum/LowVolatility/Commodities.py) con dos cambios
documentados y medibles:
  1. Momentum: el filtro 'Sharpe 12m' usa volatilidad de 12 meses (como dice la regla y como se opera).
     El backtest original usaba, por error, la volatilidad del último mes (vol_sharpe="1m" lo reproduce).
  2. Commodities: se puede correr con el universo original de 3 ETF para medir el efecto de haber
     ampliado el universo a 5 mirando el backtest (sesgo de selección; ver validacion.py).
"""
import numpy as np
import pandas as pd
import datos as D
from config import MOM, LV, CMD, COSTO_POR_LADO, CONVENCION_COSTO_UN_LADO, FIN_DATOS

def _costo(prev, new):
    tw = sum(abs(new.get(n, 0) - prev.get(n, 0)) for n in set(prev) | set(new))
    return (0.5 * tw if CONVENCION_COSTO_UN_LADO else tw) * COSTO_POR_LADO

def _elegir(ordenados, sec, top_n, max_sector):
    ch, sw = [], {}
    for tk in ordenados:
        if len(ch) >= top_n: break
        s = sec.get(tk, "Desconocido")
        if sw.get(s, 0) + 1 / top_n > max_sector + 1e-9 and s in sw: continue
        ch.append(tk); sw[s] = sw.get(s, 0) + 1 / top_n
    return ch

def _bucle(fechas, seleccion, r1, bil_r1, guardar=None):
    """Motor común: pesos decididos en t, retorno en t+1, costo sobre la rotación."""
    prev, rows = {}, []
    for i, t in enumerate(fechas):
        h = seleccion(t)
        if guardar is not None: guardar[t] = h
        if i == 0: prev = h; rows.append((t, 0.0, len(h))); continue
        if i + 1 >= len(fechas): break
        tn = fechas[i + 1]
        if not prev: g = bil_r1.get(tn, 0.0) or 0.0
        else:
            fr = r1.loc[tn] if tn in r1.index else pd.Series(dtype=float)
            g = sum(w * (0.0 if pd.isna(fr.get(k, np.nan)) else fr.get(k)) for k, w in prev.items())
        rows.append((tn, g - _costo(prev, h), len(h))); prev = h
    return pd.DataFrame(rows, columns=["fecha", "retorno", "n_posiciones"]).set_index("fecha")

def momentum_acciones(vol_sharpe=None, guardar=None, **over):
    p = dict(MOM, **over); vol_sharpe = vol_sharpe or p["vol_sharpe"]
    m = D.membresia(); px, vo = D.precios_sp500(); sec = D.sectores(); bil = D.etf_nucleo()["BIL"]
    me = px.resample("ME").last(); adv = (px * vo).rolling(60, min_periods=40).mean().resample("ME").last()
    mm = px.rolling(200, min_periods=150).mean().resample("ME").last(); dr = px.pct_change(fill_method=None)
    r1, r3, r6, r12 = (me.pct_change(k, fill_method=None) for k in (1, 3, 6, 12))
    vol = (dr.resample("ME").std() if vol_sharpe == "1m" else dr.rolling(252, min_periods=180).std().resample("ME").last()) * np.sqrt(252)
    bil_r1 = bil.resample("ME").last().pct_change()
    fechas = list(me.index[me.index >= p["inicio"]])
    def sel(t):
        u = [c for c in me.columns if c in D.universo_en(m, t.strftime("%Y-%m-%d"))]
        e = pd.DataFrame({"r3": r3.loc[t, u], "r6": r6.loc[t, u], "r12": r12.loc[t, u], "px": me.loc[t, u],
                          "mm": mm.loc[t, u], "adv": adv.loc[t, u], "vol": vol.loc[t, u]}).dropna()
        rf = bil_r1.loc[:t].tail(12).mean() * 12
        sh = (e.r12 - rf) / e.vol.replace(0, np.nan)
        e = e[(e.r3 > p["th_r3"]) & (e.r6 > p["th_r6"]) & (e.r12 > p["th_r12"]) & (e.px > e.mm) & (e.adv >= p["adv_min"]) & (sh >= p["sharpe_min"])]
        if e.empty: return {}
        sc = 0.5 * e.r6.rank(pct=True) + 0.5 * e.r12.rank(pct=True)
        ch = _elegir(sc.sort_values(ascending=False).head(p["top_n"] * 2).index, sec, p["top_n"], p["max_sector"])
        return {k: 1 / len(ch) for k in ch}
    return _bucle(fechas, sel, r1, bil_r1, guardar)

def low_volatility(guardar=None, **over):
    p = dict(LV, **over)
    m = D.membresia(); px, vo = D.precios_sp500(); sec = D.sectores(); bil = D.etf_nucleo()["BIL"]
    me = px.resample("ME").last(); r1 = me.pct_change(1, fill_method=None)
    adv = (px * vo).rolling(60, min_periods=40).mean().resample("ME").last()
    v12 = px.pct_change(fill_method=None).rolling(252, min_periods=180).std().resample("ME").last() * np.sqrt(252)
    bil_r1 = bil.resample("ME").last().pct_change(); fechas = list(me.index[me.index >= p["inicio"]])
    def sel(t):
        u = [c for c in me.columns if c in D.universo_en(m, t.strftime("%Y-%m-%d"))]
        e = pd.DataFrame({"v": v12.loc[t, u], "p": me.loc[t, u], "a": adv.loc[t, u]}).dropna()
        e = e[(e.p >= p["precio_min"]) & (e.a >= p["adv_min"])].sort_values("v")
        ch = _elegir(e.index, sec, p["top_n"], p["max_sector"])
        return {k: 1 / len(ch) for k in ch} if ch else {}
    return _bucle(fechas, sel, r1, bil_r1, guardar)

def momentum_commodities(universo=None, guardar=None, **over):
    p = dict(CMD, **over); u = universo or p["universo"]
    core = D.etf_nucleo(); px = core[u].loc[:FIN_DATOS]; bil = core["BIL"]
    me = px.resample("ME").last(); mm = px.rolling(200, min_periods=150).mean().resample("ME").last()
    v12 = px.pct_change().rolling(252, min_periods=180).std().resample("ME").last() * np.sqrt(252)
    r1, r3, r6, r12 = (me.pct_change(k) for k in (1, 3, 6, 12))
    bil_r1 = bil.resample("ME").last().pct_change(); fechas = list(me.index[me.index >= p["inicio"]])
    def sel(t):
        e = pd.DataFrame({"r3": r3.loc[t], "r6": r6.loc[t], "r12": r12.loc[t], "px": me.loc[t], "mm": mm.loc[t], "v": v12.loc[t]}).dropna()
        e = e[(e.r3 > p["th_r3"]) & (e.r6 > p["th_r6"]) & (e.r12 > p["th_r12"]) & (e.px > e.mm) & (e.v < p["vol_max"])]
        return {k: 1 / len(e) for k in e.index} if len(e) else {}
    return _bucle(fechas, sel, r1, bil_r1, guardar)
