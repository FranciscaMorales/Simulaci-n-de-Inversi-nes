"""Rotación semanal por momentum de 8 semanas con comisión fija de USD 10 por operación.
Compara tamaños de canasta (N) y una banda de permanencia (una acción se vende solo si cae
fuera del top 2N) para cumplir la rúbrica de StockTrak (>= 5 operaciones/semana, 150-300 en
12 semanas) al menor costo. Además lista lo que el modelo habría elegido a fines de agosto 2026
en Low-Volatility y en la rotación, para comparar con la cartera real."""
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "datos")
OUT = os.path.join(HERE, "..", "resultados", "rotacion_comision")
os.makedirs(OUT, exist_ok=True)

CAPITAL = 0.0853867537373288 * 144_000  # tramo de rotación del BL auditado
COMISION = 10.0
LOOKBACK = 8

px = pd.read_parquet(os.path.join(DATA, "sp500_prices.parquet"))
vol = pd.read_parquet(os.path.join(DATA, "sp500_volumes.parquet")).reindex(px.index)
mem = pd.read_csv(os.path.join(DATA, "sp500_membership.csv"), parse_dates=["date"]).set_index("date")["tickers"]


def miembros(t):
    return set(mem.loc[:t].iloc[-1].split(","))


semana = px.resample("W-FRI").last()
r1 = semana.pct_change(fill_method=None)
mom = semana.pct_change(LOOKBACK, fill_method=None)
adv = (px * vol).rolling(60, min_periods=40).mean().resample("W-FRI").last()
fechas = [d for d in semana.index if d >= pd.Timestamp("2013-01-01")]
ranking = {}
for t in fechas:
    cols = [c for c in semana.columns if c in miembros(t)]
    x = pd.DataFrame({"m": mom.loc[t, cols], "p": semana.loc[t, cols], "a": adv.loc[t, cols]}).dropna()
    x = x[(x.p >= 5) & (x.a >= 5e6)]
    ranking[t] = list(x["m"].sort_values(ascending=False).index)


def backtest(n, banda):
    valor, held, filas = CAPITAL, [], []
    for i, t in enumerate(fechas[:-1]):
        rk = ranking[t]
        limite = set(rk[: 2 * n]) if banda else set(rk[:n])
        keep = [h for h in held if h in limite]
        nuevos = [c for c in rk if c not in keep][: n - len(keep)]
        ops = (len(held) - len(keep)) + len(nuevos)
        held = keep + nuevos
        fwd = r1.loc[fechas[i + 1], held].fillna(0.0).clip(-0.9, 2.0).mean() if held else 0.0
        filas.append((fechas[i + 1], fwd, ops))
    df = pd.DataFrame(filas, columns=["fecha", "bruto", "ops"]).set_index("fecha")
    ops = df["ops"].iloc[1:]  # sin la compra inicial
    # comisión como % del tramo (capital constante de USD 12.296 cada semana)
    ret = df["bruto"] - df["ops"] * COMISION / CAPITAL
    tw = ops.rolling(12).sum().dropna()
    return {"N": n, "banda_2N": banda, "ops_semana": ops.mean(), "semanas_<5_ops": (ops < 5).mean(),
            "ops_12_semanas_mediana": tw.median(), "ops_12_semanas_min": tw.min(),
            "comision_12_semanas_USD": tw.median() * COMISION, "posicion_USD": CAPITAL / n,
            "retorno_bruto_anual": df["bruto"].mean() * 52,
            "costo_comision_anual": ops.mean() * 52 * COMISION / CAPITAL,
            "retorno_neto_anual": ret.iloc[1:].mean() * 52, "vol_anual": df["bruto"].std() * np.sqrt(52)}


res = pd.DataFrame([backtest(n, b) for n in (10, 15, 20, 30) for b in (False, True)])
res.to_csv(os.path.join(OUT, "variantes.csv"), index=False)
pd.set_option("display.width", 200)
print(res.round(3).to_string(index=False))

# Lo que el modelo habría elegido a fines de agosto 2026
t = fechas[-1]
print("\nRotación top 30 (momentum 8 semanas) al", t.date(), ":", ranking[t][:30])
sec = pd.read_csv(os.path.join(DATA, "sector_map.csv")).set_index("Symbol")["GICS Sector"] \
    if os.path.exists(os.path.join(DATA, "sector_map.csv")) else pd.Series(dtype=str)
fin = pd.Timestamp("2026-08-31")
v12 = px.loc[:fin].pct_change(fill_method=None).iloc[-252:].std() * np.sqrt(252)
cols = [c for c in px.columns if c in miembros(fin)]
cand = pd.DataFrame({"vol": v12[cols], "p": px.loc[:fin, cols].iloc[-1],
                     "a": (px * vol).loc[:fin, cols].iloc[-60:].mean()}).dropna()
cand = cand[(cand.p >= 5) & (cand.a >= 5e6)].sort_values("vol")
elegidas, cuenta = [], {}
for tk in cand.index:
    s = sec.get(tk, "Desconocido")
    if cuenta.get(s, 0) >= 2 and s != "Desconocido":
        continue
    elegidas.append(tk)
    cuenta[s] = cuenta.get(s, 0) + 1
    if len(elegidas) == 10:
        break
print("Low-Vol top 10 (vol 12m, máx 25% por sector) al", fin.date(), ":")
print(cand.loc[elegidas, "vol"].round(4).to_string())
