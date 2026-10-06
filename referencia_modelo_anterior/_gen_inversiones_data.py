"""
Genera los datos (precios, ATR, stop-loss, tamano de posicion) para el PDF
Inversiones.pdf. Reusa la logica de senales de Senales_Hoy.py y le agrega:
  - precio actual y ATR(14) de cada posicion
  - stop-loss sugerido = precio - 2 x ATR(14) (metodo estandar de trend
    following / momentum, se adapta a la volatilidad real de cada activo)
  - monto en USD y numero de acciones por posicion, dado el capital
    asignado a cada sleeve (pesos Black-Litterman x capital invertible) y
    un costo de transaccion fijo de USD 10 por posicion
No es parte del backtest -- es una utilidad de ejecucion, se corre aparte
cada vez que se arma o rebalancea la cartera.
"""
import datetime
import json
import os

import numpy as np
import openpyxl
import pandas as pd
import yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__))
XLSX_PATH = os.path.join(HERE, "Modelo_Nexum_Final.xlsx")
SECTOR_MAP_CSV = os.path.join(HERE, "sector_map.csv")
MEMBERSHIP_CSV = os.path.join(HERE, "sp500_membership.csv")

ASSET_ORDER = ["SPY", "TLH", "VCLT", "MOM_CMD", "MOM_EQ", "LOW_VOL"]
COMMODITIES = ["GLD", "USO", "DBA", "SLV", "CPER"]
CAPITAL_INVERTIBLE = 144_000.0
COSTO_TRANSACCION = 10.0
PRICE_MIN = 5.0
ADV_MIN = 5_000_000
TOP_N = 10
MAX_SECTOR_WEIGHT = 0.25
MOM_TH_R3, MOM_TH_R6, MOM_TH_R12, MOM_SHARPE_MIN = 0.00, 0.05, 0.10, 0.5
CMD_TH_R3, CMD_TH_R6, CMD_TH_R12, CMD_VOL_MAX = 0.05, 0.08, 0.10, 0.50
ATR_MULT = 2.0


def load_sector_map():
    df = pd.read_csv(SECTOR_MAP_CSV)
    return dict(zip(df["Symbol"], df["GICS Sector"]))


def current_universe():
    mem = pd.read_csv(MEMBERSHIP_CSV)
    last = mem.iloc[-1]
    return [t.strip() for t in last["tickers"].split(",") if t.strip()], last["date"]


def download_ohlc(tickers, lookback_days=420):
    end = datetime.date.today() + datetime.timedelta(days=1)
    start = end - datetime.timedelta(days=lookback_days)
    closes, highs, lows, volumes = {}, {}, {}, {}
    chunk_size = 80
    for i in range(0, len(tickers), chunk_size):
        chunk = tickers[i:i + chunk_size]
        try:
            data = yf.download(chunk, start=start, end=end, progress=False,
                                group_by="ticker", threads=True, auto_adjust=True)
        except Exception:
            continue
        for t in chunk:
            try:
                sub = data[t] if len(chunk) > 1 else data
                c, h, l, v = sub["Close"].dropna(), sub["High"].dropna(), sub["Low"].dropna(), sub["Volume"].dropna()
                if len(c) > 0:
                    closes[t] = c
                    highs[t] = h
                    lows[t] = l
                    volumes[t] = v
            except Exception:
                pass
    return pd.DataFrame(closes), pd.DataFrame(highs), pd.DataFrame(lows), pd.DataFrame(volumes)


def atr14(close, high, low):
    prev_close = close.shift(1)
    tr = pd.concat([(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    return tr.rolling(14).mean()


def momentum_signal(close, volumes, bil):
    r3 = close.iloc[-1] / close.iloc[-64] - 1 if len(close) > 64 else pd.Series(dtype=float)
    r6 = close.iloc[-1] / close.iloc[-127] - 1 if len(close) > 127 else pd.Series(dtype=float)
    r12 = close.iloc[-1] / close.iloc[-253] - 1 if len(close) > 253 else pd.Series(dtype=float)
    mm200 = close.tail(200).mean()
    adv = (close * volumes).tail(60).mean()
    vol12 = close.pct_change().tail(252).std() * np.sqrt(252)
    bil_r1 = bil.pct_change().tail(252)
    rf12 = bil_r1.mean() * 252 if len(bil_r1) else 0.0
    elig = pd.DataFrame({"r3": r3, "r6": r6, "r12": r12, "px": close.iloc[-1],
                          "mm200": mm200, "adv": adv, "vol12": vol12}).dropna()
    sharpe12 = (elig["r12"] - rf12) / elig["vol12"].replace(0, np.nan)
    mask = ((elig["r3"] > MOM_TH_R3) & (elig["r6"] > MOM_TH_R6) & (elig["r12"] > MOM_TH_R12)
            & (elig["px"] > elig["mm200"]) & (elig["adv"] >= ADV_MIN) & (sharpe12 >= MOM_SHARPE_MIN))
    elig = elig[mask]
    score = (0.5 * elig["r6"].rank(pct=True) + 0.5 * elig["r12"].rank(pct=True)) if not elig.empty else pd.Series(dtype=float)
    return elig, score


def lowvol_signal(close, volumes):
    vol12 = close.pct_change().tail(252).std() * np.sqrt(252)
    adv = (close * volumes).tail(60).mean()
    elig = pd.DataFrame({"vol": vol12, "px": close.iloc[-1], "adv": adv}).dropna()
    mask = (elig["px"] >= PRICE_MIN) & (elig["adv"] >= ADV_MIN)
    return elig[mask]


def pick_top_n(elig, score, sector_map, top_n=TOP_N, ascending=False):
    order = score.sort_values(ascending=ascending)
    chosen, sector_w = [], {}
    for tk in order.index:
        if len(chosen) >= top_n:
            break
        sec = sector_map.get(tk, "Desconocido")
        if sector_w.get(sec, 0) + 1 / top_n > MAX_SECTOR_WEIGHT + 1e-9 and sec in sector_w:
            continue
        chosen.append(tk)
        sector_w[sec] = sector_w.get(sec, 0) + 1 / top_n
    return chosen


def commodities_signal():
    data = yf.download(COMMODITIES, period="500d", progress=False, auto_adjust=True)
    px = data["Close"]
    high = data["High"]
    low = data["Low"]
    daily_ret = px.pct_change()
    r3 = px.iloc[-1] / px.iloc[-64] - 1
    r6 = px.iloc[-1] / px.iloc[-127] - 1
    r12 = px.iloc[-1] / px.iloc[-253] - 1
    mm200 = px.tail(200).mean()
    vol12 = daily_ret.tail(252).std() * np.sqrt(252)
    elig = pd.DataFrame({"r3": r3, "r6": r6, "r12": r12, "px": px.iloc[-1], "mm200": mm200, "vol": vol12}).dropna()
    mask = (elig["r3"] > CMD_TH_R3) & (elig["r6"] > CMD_TH_R6) & (elig["r12"] > CMD_TH_R12) & (elig["px"] > elig["mm200"]) & (elig["vol"] < CMD_VOL_MAX)
    chosen = list(elig[mask].index)
    return chosen, px, high, low


def load_bl_weights():
    wb = openpyxl.load_workbook(XLSX_PATH, data_only=False)
    ws = wb["09b_Black_Litterman"]
    return {name: ws[f"D{62+i}"].value for i, name in enumerate(ASSET_ORDER)}


def core_etf_prices():
    data = yf.download(["SPY", "TLH", "VCLT"], period="30d", progress=False, auto_adjust=True)["Close"]
    return {t: float(data[t].dropna().iloc[-1]) for t in ["SPY", "TLH", "VCLT"]}


def size_positions(picks, sleeve_capital, prices, stops):
    n = len(picks)
    if n == 0:
        return []
    capital_por_posicion = sleeve_capital / n
    rows = []
    for tk in picks:
        px = prices[tk]
        neto = capital_por_posicion - COSTO_TRANSACCION
        acciones = int(neto // px) if neto > 0 else 0
        invertido = acciones * px
        efectivo_sobrante = capital_por_posicion - invertido - COSTO_TRANSACCION
        rows.append({
            "ticker": tk, "precio": px, "capital_bruto": capital_por_posicion,
            "acciones": acciones, "invertido": invertido, "sobrante": efectivo_sobrante,
            "stop_loss": stops.get(tk),
        })
    return rows


def main():
    weights = load_bl_weights()
    universe, snap_date = current_universe()
    close, high, low, volumes = download_ohlc(universe)
    bil = yf.download("BIL", period="500d", progress=False, auto_adjust=True)["Close"]
    if isinstance(bil, pd.DataFrame):
        bil = bil["BIL"]
    sector_map = load_sector_map()

    elig_mom, score_mom = momentum_signal(close, volumes, bil)
    picks_mom = pick_top_n(elig_mom, score_mom, sector_map, TOP_N, ascending=False) if not elig_mom.empty else []

    elig_lv = lowvol_signal(close, volumes)
    picks_lv = pick_top_n(elig_lv, elig_lv["vol"] if not elig_lv.empty else pd.Series(dtype=float), sector_map, TOP_N, ascending=True) if not elig_lv.empty else []

    picks_cmd, px_cmd, high_cmd, low_cmd = commodities_signal()

    all_stock_picks = list(set(picks_mom) | set(picks_lv))
    atr_stock = {}
    for tk in all_stock_picks:
        a = atr14(close[tk], high[tk], low[tk])
        atr_stock[tk] = float(a.iloc[-1]) if not a.empty and not pd.isna(a.iloc[-1]) else None
    prices_stock = {tk: float(close[tk].iloc[-1]) for tk in all_stock_picks}
    stops_stock = {tk: (prices_stock[tk] - ATR_MULT * atr_stock[tk]) if atr_stock[tk] else None for tk in all_stock_picks}

    atr_cmd = {}
    for tk in picks_cmd:
        a = atr14(px_cmd[tk], high_cmd[tk], low_cmd[tk])
        atr_cmd[tk] = float(a.iloc[-1]) if not a.empty and not pd.isna(a.iloc[-1]) else None
    prices_cmd = {tk: float(px_cmd[tk].iloc[-1]) for tk in picks_cmd}
    stops_cmd = {tk: (prices_cmd[tk] - ATR_MULT * atr_cmd[tk]) if atr_cmd[tk] else None for tk in picks_cmd}

    core_px = core_etf_prices()

    cap_mom = CAPITAL_INVERTIBLE * weights["MOM_EQ"]
    cap_lv = CAPITAL_INVERTIBLE * weights["LOW_VOL"]
    cap_cmd = CAPITAL_INVERTIBLE * weights["MOM_CMD"]
    cap_spy = CAPITAL_INVERTIBLE * weights["SPY"]
    cap_tlh = CAPITAL_INVERTIBLE * weights["TLH"]
    cap_vclt = CAPITAL_INVERTIBLE * weights["VCLT"]

    rows_mom = size_positions(picks_mom, cap_mom, prices_stock, stops_stock)
    rows_lv = size_positions(picks_lv, cap_lv, prices_stock, stops_stock)
    rows_cmd = size_positions(picks_cmd, cap_cmd, prices_cmd, stops_cmd)

    core_rows = []
    for tk, cap in [("SPY", cap_spy), ("TLH", cap_tlh), ("VCLT", cap_vclt)]:
        px = core_px[tk]
        neto = cap - COSTO_TRANSACCION
        acciones = int(neto // px) if neto > 0 else 0
        invertido = acciones * px
        core_rows.append({"ticker": tk, "precio": px, "capital_bruto": cap, "acciones": acciones,
                           "invertido": invertido, "sobrante": cap - invertido - COSTO_TRANSACCION})

    out = {
        "fecha": str(datetime.date.today()),
        "snap_membership": str(snap_date),
        "capital_invertible": CAPITAL_INVERTIBLE,
        "costo_transaccion": COSTO_TRANSACCION,
        "weights": weights,
        "core_rows": core_rows,
        "rows_mom": rows_mom,
        "rows_lv": rows_lv,
        "rows_cmd": rows_cmd,
        "cap_mom": cap_mom, "cap_lv": cap_lv, "cap_cmd": cap_cmd,
        "cap_spy": cap_spy, "cap_tlh": cap_tlh, "cap_vclt": cap_vclt,
    }
    with open(os.path.join(HERE, "_inversiones_data.json"), "w") as f:
        json.dump(out, f, indent=2, default=str)
    print("Datos guardados en _inversiones_data.json")
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
