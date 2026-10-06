"""
Modelo Nexum - Senales de HOY para partir invirtiendo en StockTrak.

A diferencia de los Backtesting_*.py (que reconstruyen la historia completa
2010-2026 para medir Sharpe/CAGR), este script corre las mismas reglas de
cada estrategia UNA sola vez, con los datos mas recientes disponibles, y
entrega la canasta concreta a comprar hoy: 10 acciones de Momentum, 10 de
Low-Volatility, hasta 5 ETF de Commodities, y el recordatorio del nucleo
pasivo (SPY/TLH/VCLT). Usa datos frescos (no el cache congelado del
14-sep-2026 que usan los backtests) para que los precios y la elegibilidad
reflejen el mercado de HOY.

Reglas replicadas (mismos parametros que los backtests -- ver
06_Parametros_Estrategias):
  - Momentum de acciones: Backtesting_Momentum.py (r3>0%, r6>5%, r12>10%,
    precio>MM200, ADV>=5M, Sharpe12m>=0.5 vs BIL; top-10 por score
    50% r6m + 50% r12m, equal-weight, max 25%/sector).
  - Low-Volatility: Backtesting_LowVolatility.py (precio>=5, ADV>=5M;
    top-10 por menor volatilidad realizada 12m, equal-weight, max 25%/sector).
  - Commodities: Backtesting_Commodities.py (GLD/USO/DBA/SLV/CPER; r3>5%,
    r6>8%, r12>10%, precio>MM200, vol12m<50%; todos los elegibles,
    equal-weight, hasta 5).

Los pesos de sleeve (cuanto capital va a cada pieza) son los de
09b_Black_Litterman!D62:D67 -- la asignacion recomendada del modelo.

Uso: python3 Senales_Hoy.py
Requiere: pandas, numpy, yfinance, openpyxl
Descarga datos frescos de Yahoo Finance (no usa el cache de los backtests).
"""

import datetime
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
PRICE_MIN = 5.0
ADV_MIN = 5_000_000
TOP_N = 10
MAX_SECTOR_WEIGHT = 0.25
MOM_TH_R3, MOM_TH_R6, MOM_TH_R12, MOM_SHARPE_MIN = 0.00, 0.05, 0.10, 0.5
CMD_TH_R3, CMD_TH_R6, CMD_TH_R12, CMD_VOL_MAX = 0.05, 0.08, 0.10, 0.50


def load_sector_map():
    df = pd.read_csv(SECTOR_MAP_CSV)
    return dict(zip(df["Symbol"], df["GICS Sector"]))


def current_universe():
    mem = pd.read_csv(MEMBERSHIP_CSV)
    last = mem.iloc[-1]
    print(f"Universo S&P 500: snapshot del {last['date']} ({(pd.Timestamp.today() - pd.Timestamp(last['date'])).days} dias de antiguedad -- verificar cambios recientes de indice antes de operar).")
    return [t.strip() for t in last["tickers"].split(",") if t.strip()]


def download_recent_prices(tickers, lookback_days=420):
    end = datetime.date.today() + datetime.timedelta(days=1)
    start = end - datetime.timedelta(days=lookback_days)
    print(f"Descargando precios recientes de {len(tickers)} tickers ({start} a {end})...")
    closes, volumes = {}, {}
    chunk_size = 80
    for i in range(0, len(tickers), chunk_size):
        chunk = tickers[i:i + chunk_size]
        try:
            data = yf.download(chunk, start=start, end=end, progress=False,
                                group_by="ticker", threads=True, auto_adjust=True)
        except Exception as e:
            print(f"  chunk {i} fallo: {e}")
            continue
        for t in chunk:
            try:
                sub = data[t] if len(chunk) > 1 else data
                c = sub["Close"].dropna()
                v = sub["Volume"].dropna()
                if len(c) > 0:
                    closes[t] = c
                    volumes[t] = v
            except Exception:
                pass
    return pd.DataFrame(closes), pd.DataFrame(volumes)


def momentum_signal(prices, volumes, bil):
    t = prices.index[-1]
    daily_ret = prices.pct_change()
    r3 = prices.iloc[-1] / prices.iloc[-64] - 1 if len(prices) > 64 else pd.Series(dtype=float)
    r6 = prices.iloc[-1] / prices.iloc[-127] - 1 if len(prices) > 127 else pd.Series(dtype=float)
    r12 = prices.iloc[-1] / prices.iloc[-253] - 1 if len(prices) > 253 else pd.Series(dtype=float)
    mm200 = prices.tail(200).mean()
    adv = (prices * volumes).tail(60).mean()
    vol12 = daily_ret.tail(252).std() * np.sqrt(252)
    bil_r1 = bil.pct_change().tail(252)
    rf12 = bil_r1.mean() * 252 if len(bil_r1) else 0.0

    elig = pd.DataFrame({"r3": r3, "r6": r6, "r12": r12, "px": prices.iloc[-1],
                          "mm200": mm200, "adv": adv, "vol12": vol12}).dropna()
    sharpe12 = (elig["r12"] - rf12) / elig["vol12"].replace(0, np.nan)
    mask = ((elig["r3"] > MOM_TH_R3) & (elig["r6"] > MOM_TH_R6) & (elig["r12"] > MOM_TH_R12)
            & (elig["px"] > elig["mm200"]) & (elig["adv"] >= ADV_MIN) & (sharpe12 >= MOM_SHARPE_MIN))
    elig = elig[mask]
    return t, elig, (0.5 * elig["r6"].rank(pct=True) + 0.5 * elig["r12"].rank(pct=True)) if not elig.empty else pd.Series(dtype=float)


def lowvol_signal(prices, volumes):
    t = prices.index[-1]
    daily_ret = prices.pct_change()
    vol12 = daily_ret.tail(252).std() * np.sqrt(252)
    adv = (prices * volumes).tail(60).mean()
    elig = pd.DataFrame({"vol": vol12, "px": prices.iloc[-1], "adv": adv}).dropna()
    mask = (elig["px"] >= PRICE_MIN) & (elig["adv"] >= ADV_MIN)
    return t, elig[mask]


def pick_top_n(elig, score, sector_map, top_n=TOP_N, ascending_score=False):
    order = score.sort_values(ascending=ascending_score)
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
    px = yf.download(COMMODITIES, period="500d", progress=False, auto_adjust=True)["Close"]
    daily_ret = px.pct_change()
    r3 = px.iloc[-1] / px.iloc[-64] - 1
    r6 = px.iloc[-1] / px.iloc[-127] - 1
    r12 = px.iloc[-1] / px.iloc[-253] - 1
    mm200 = px.tail(200).mean()
    vol12 = daily_ret.tail(252).std() * np.sqrt(252)
    elig = pd.DataFrame({"r3": r3, "r6": r6, "r12": r12, "px": px.iloc[-1], "mm200": mm200, "vol": vol12}).dropna()
    mask = (elig["r3"] > CMD_TH_R3) & (elig["r6"] > CMD_TH_R6) & (elig["r12"] > CMD_TH_R12) & (elig["px"] > elig["mm200"]) & (elig["vol"] < CMD_VOL_MAX)
    chosen = list(elig[mask].index)
    return px.index[-1], chosen


def load_bl_weights():
    wb = openpyxl.load_workbook(XLSX_PATH, data_only=False)
    ws = wb["09b_Black_Litterman"]
    return {name: ws[f"D{62+i}"].value for i, name in enumerate(ASSET_ORDER)}


def pct(x):
    return f"{100*x:.2f}%"


def main():
    weights = load_bl_weights()
    print("=== MODELO NEXUM - SEÑALES DE HOY (para StockTrak) ===\n")
    print(f"Fecha de corrida: {datetime.date.today()}\n")
    print("Pesos de sleeve (09b_Black_Litterman!D62:D67, asignación recomendada):")
    for k in ASSET_ORDER:
        print(f"  {k}: {pct(weights[k])}")
    print()

    # --- Núcleo pasivo ---
    print("1. NÚCLEO PASIVO (implementación directa, sin señal que calcular)")
    for tk, key in [("SPY", "SPY"), ("TLH", "TLH"), ("VCLT", "VCLT")]:
        print(f"   {tk}: {pct(weights[key])} del capital total")
    print()

    # --- Universo y datos frescos de acciones ---
    tickers = current_universe()
    prices, volumes = download_recent_prices(tickers)
    bil = yf.download("BIL", period="500d", progress=False, auto_adjust=True)["Close"]
    if isinstance(bil, pd.DataFrame):
        bil = bil["BIL"]
    sector_map = load_sector_map()

    # --- Momentum de acciones ---
    t_mom, elig_mom, score_mom = momentum_signal(prices, volumes, bil)
    picks_mom = pick_top_n(elig_mom, score_mom, sector_map, TOP_N, ascending_score=False) if not elig_mom.empty else []
    w_in_sleeve = 1 / len(picks_mom) if picks_mom else 0
    w_total = weights["MOM_EQ"] * w_in_sleeve
    print(f"2. MOMENTUM DE ACCIONES (señal al {t_mom.date()}, {len(picks_mom)} posiciones)")
    print(f"   Peso de sleeve: {pct(weights['MOM_EQ'])} del capital total")
    for tk in picks_mom:
        print(f"   {tk}: {pct(w_in_sleeve)} del sleeve  |  {pct(w_total)} del capital total")
    if not picks_mom:
        print("   Sin señal suficiente hoy -- este tramo iría 100% a BIL/SGOV hasta el próximo rebalanceo mensual.")
    print()

    # --- Low-Volatility ---
    t_lv, elig_lv = lowvol_signal(prices, volumes)
    score_lv = elig_lv["vol"] if not elig_lv.empty else pd.Series(dtype=float)
    picks_lv = pick_top_n(elig_lv, score_lv, sector_map, TOP_N, ascending_score=True) if not elig_lv.empty else []
    w_in_sleeve = 1 / len(picks_lv) if picks_lv else 0
    w_total = weights["LOW_VOL"] * w_in_sleeve
    print(f"3. LOW-VOLATILITY (señal al {t_lv.date()}, {len(picks_lv)} posiciones)")
    print(f"   Peso de sleeve: {pct(weights['LOW_VOL'])} del capital total")
    for tk in picks_lv:
        print(f"   {tk}: {pct(w_in_sleeve)} del sleeve  |  {pct(w_total)} del capital total")
    print()

    # --- Commodities ---
    t_cmd, picks_cmd = commodities_signal()
    w_in_sleeve = 1 / len(picks_cmd) if picks_cmd else 0
    w_total = weights["MOM_CMD"] * w_in_sleeve
    print(f"4. COMMODITIES (señal al {t_cmd.date()}, {len(picks_cmd)} de {len(COMMODITIES)} posibles)")
    print(f"   Peso de sleeve: {pct(weights['MOM_CMD'])} del capital total")
    for tk in picks_cmd:
        print(f"   {tk}: {pct(w_in_sleeve)} del sleeve  |  {pct(w_total)} del capital total")
    if not picks_cmd:
        print("   Sin señal suficiente hoy -- este tramo iría 100% a BIL/SGOV hasta el próximo rebalanceo mensual.")
    print()

    print("NOTA: rebalanceo mensual para Momentum, Low-Volatility y Commodities (correr este script una vez")
    print("al mes, mismo día del mes). El núcleo pasivo (SPY/TLH/VCLT) no rota. Confirmar disponibilidad de")
    print("cada ticker en StockTrak antes de operar (00_Inputs!D47).")


if __name__ == "__main__":
    main()
