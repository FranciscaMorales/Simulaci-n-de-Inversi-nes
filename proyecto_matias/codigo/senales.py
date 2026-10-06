"""Señales de operación (uso semanal/mensual): ranking de Momentum, Low-Vol y Commodities con precios frescos.

Aplica EXACTAMENTE las reglas de config.py (las mismas del backtest). Uso:  python3 senales.py
Nota: Yahoo Finance lista a Bank of New York Mellon como BNY (StockTrak: BK).
"""
import datetime
import numpy as np
import pandas as pd
import yfinance as yf
import datos as D
from config import MOM, LV, CMD

MAPA_YAHOO = {"BK": "BNY", "BRK.B": "BRK-B", "BF.B": "BF-B"}
def _descargar(tks, dias=420):
    y = [MAPA_YAHOO.get(t, t) for t in tks]; inv = {MAPA_YAHOO.get(t, t): t for t in tks}
    d = yf.download(y, period=f"{dias}d", progress=False, auto_adjust=True, group_by="column", threads=True)
    return d["Close"].rename(columns=inv), d["Volume"].rename(columns=inv)

def ranking(top=30):
    m = D.membresia(); u = sorted(D.universo_en(m, m["date"].max().strftime("%Y-%m-%d"))); sec = D.sectores()
    px, vo = _descargar(u); px = px.ffill(); l = px.iloc[-1]
    bil = yf.download("BIL", period="420d", progress=False, auto_adjust=True)["Close"].squeeze()
    r = lambda n: l / px.iloc[-1 - n] - 1
    vol12 = px.pct_change().tail(252).std() * np.sqrt(252); adv = (px * vo).tail(60).mean()
    rf = bil.pct_change().tail(252).mean() * 252
    e = pd.DataFrame({"r3": r(63), "r6": r(126), "r12": r(252), "mm": l > px.tail(200).mean(), "adv": adv, "vol12": vol12, "precio": l}).dropna()
    e["sharpe12"] = (e.r12 - rf) / e.vol12; e["sector"] = [sec.get(k, "?") for k in e.index]
    mom = e[(e.r3 > MOM["th_r3"]) & (e.r6 > MOM["th_r6"]) & (e.r12 > MOM["th_r12"]) & e.mm & (e.adv >= MOM["adv_min"]) & (e.sharpe12 >= MOM["sharpe_min"])].copy()
    mom["puntaje"] = 0.5 * mom.r6.rank(pct=True) + 0.5 * mom.r12.rank(pct=True); mom = mom.sort_values("puntaje", ascending=False)
    lv = e[(e.precio >= LV["precio_min"]) & (e.adv >= LV["adv_min"])].sort_values("vol12")
    def sel(df_, n, cap):
        ch, sw = [], {}
        for k, s in zip(df_.index, df_.sector):
            if len(ch) >= n: break
            if sw.get(s, 0) + 1 / n > cap + 1e-9 and s in sw: continue
            ch.append(k); sw[s] = sw.get(s, 0) + 1 / n
        return ch
    cpx = yf.download(CMD["universo"], period="500d", progress=False, auto_adjust=True)["Close"].ffill(); cl = cpx.iloc[-1]
    c = pd.DataFrame({"r3": cl / cpx.iloc[-64] - 1, "r6": cl / cpx.iloc[-127] - 1, "r12": cl / cpx.iloc[-253] - 1, "sobre_mm200": cl > cpx.tail(200).mean(),
                      "vol12": cpx.pct_change().tail(252).std() * np.sqrt(252)})
    c["califica"] = (c.r3 > CMD["th_r3"]) & (c.r6 > CMD["th_r6"]) & (c.r12 > CMD["th_r12"]) & c.sobre_mm200 & (c.vol12 < CMD["vol_max"])
    return {"fecha": px.index[-1].date(), "momentum": mom.head(top), "momentum_sel": sel(mom, MOM["top_n"], MOM["max_sector"]),
            "lowvol": lv.head(top), "lowvol_sel": sel(lv, LV["top_n"], LV["max_sector"]), "commodities": c}

if __name__ == "__main__":
    s = ranking(); pd.set_option("display.width", 200)
    print(f"Señales al {s['fecha']}\n\nMOMENTUM — selección: {s['momentum_sel']}"); print(s["momentum"][["sector", "r3", "r6", "r12", "sharpe12", "puntaje"]].round(3))
    print(f"\nLOW-VOL — selección: {s['lowvol_sel']}"); print(s["lowvol"][["sector", "vol12"]].round(3))
    print("\nCOMMODITIES"); print(s["commodities"].round(3))
