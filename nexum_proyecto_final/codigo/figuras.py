"""Gráficos del informe (PNG, 200 dpi). Paleta categórica validada (orden fijo): azul, naranja, aqua, amarillo."""
import os
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from config import RESULTADOS, BASE, NOMBRES, ACTIVOS, PESOS_APROBADOS
OUT = os.path.join(BASE, "informe", "figuras"); os.makedirs(OUT, exist_ok=True)
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]; SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
plt.rcParams.update({"font.family": "Arial", "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.facecolor": SURF, "figure.facecolor": SURF, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
                     "axes.spines.top": False, "axes.axisbelow": True, "axes.spines.right": False, "legend.frameon": False})
S = pd.read_pickle(os.path.join(RESULTADOS, "estado.pkl")); T = S["T"]
def save(fig, n): fig.tight_layout(); fig.savefig(os.path.join(OUT, n), dpi=200); plt.close(fig)

# 1. Crecimiento de USD 100 (2016-2026)
r = pd.DataFrame({"Cartera Nexum": S["port"], "Benchmark de política": S["bench"], "AGF actual 85/15": S["agf"], "S&P 500": S["df"].SPY}).loc["2016-01-31":]
w = 100 * (1 + r).cumprod()
fig, ax = plt.subplots(figsize=(7.2, 3.4))
for i, c in enumerate(w.columns):
    ax.plot(w.index, w[c], color=C[i], lw=2 if i == 0 else 1.4, label=c)
    ax.annotate(f"{w[c].iloc[-1]:.0f}", (w.index[-1], w[c].iloc[-1]), xytext=(4, 0), textcoords="offset points", va="center", color=INK, fontsize=8)
ax.set_ylabel("Valor de USD 100 invertidos"); ax.legend(loc="upper left", ncol=2); ax.set_title("Crecimiento de USD 100, ene-2016 a ago-2026 (USD nominal)", loc="left", color=INK, fontsize=10)
save(fig, "f1_crecimiento.png")

# 2. Caídas desde el máximo
fig, ax = plt.subplots(figsize=(7.2, 2.6))
for i, c in enumerate(["Cartera Nexum", "AGF actual 85/15"]):
    dd = w[c] / w[c].cummax() - 1; ax.plot(dd.index, dd * 100, color=C[0 if i == 0 else 2], lw=1.6, label=c)
ax.set_ylabel("Caída desde el máximo (%)"); ax.legend(loc="lower left"); ax.set_title("Caídas desde el máximo: Nexum vs. cartera actual de la AGF", loc="left", color=INK, fontsize=10)
save(fig, "f2_caidas.png")

# 3. Asignación: aprobada vs prior vs Markowitz
a = T["Asignacion"]; lab = [NOMBRES[x].replace(" (", "\n(") for x in ACTIVOS]; y = np.arange(len(ACTIVOS)); h = 0.26
fig, ax = plt.subplots(figsize=(7.2, 3.6))
for k, (col, nm) in enumerate([("Pesos aprobados (en implementación)", "Black-Litterman (aprobado)"), ("Prior paridad de riesgo", "Prior de paridad de riesgo"), ("Markowitz histórico", "Markowitz histórico")]):
    ax.barh(y + (k - 1) * h, a[col] * 100, height=h - 0.03, color=C[k], label=nm)
for i, v in enumerate(a["Pesos aprobados (en implementación)"]): ax.annotate(f"{v*100:.1f}%", (v * 100, i - h), xytext=(3, 0), textcoords="offset points", va="center", fontsize=7.5, color=INK)
ax.set_yticks(y); ax.set_yticklabels(lab); ax.invert_yaxis(); ax.set_xlabel("Peso (%)"); ax.legend(loc="lower right")
ax.set_title("Asignación estratégica: Black-Litterman frente a sus referencias", loc="left", color=INK, fontsize=10); save(fig, "f3_asignacion.png")

# 4. Montecarlo: probabilidad por objetivo
mc = T["Montecarlo"]; objs = ["P(Educación)", "P(Villarrica)", "P(Herencia)", "P(3 objetivos)"]
esc = [("Nexum", "Hist", "USD", "Nexum · histórico"), ("Nexum", "Prosp", "USD", "Nexum · prospectivo"), ("AGF 85/15", "Prosp", "USD", "AGF · prospectivo"), ("Nexum", "Prosp", "UF", "Nexum · prospectivo en UF")]
x = np.arange(len(objs)); h = 0.2
fig, ax = plt.subplots(figsize=(7.2, 3.2))
for k, (cart, e, mon, nm) in enumerate(esc):
    v = mc[(mc.Cartera == cart) & mc.Escenario.str.startswith(e) & (mc.Moneda == mon)][objs].iloc[0].values * 100
    ax.bar(x + (k - 1.5) * h, v, width=h - 0.03, color=C[k], label=nm)
    if k in (0, 1):
        for i, vv in enumerate(v): ax.annotate(f"{vv:.0f}%", (x[i] + (k - 1.5) * h, vv), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=7, color=INK)
ax.set_xticks(x); ax.set_xticklabels(["Educación", "Villarrica", "Herencia", "Los 3 objetivos"]); ax.set_ylabel("Probabilidad (%)"); ax.set_ylim(0, 110)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=4, fontsize=7.5); ax.set_title("Montecarlo (20.000 escenarios): probabilidad de cumplir cada objetivo", loc="left", color=INK, fontsize=10)
save(fig, "f4_montecarlo.png")

# 5. TIR requerida por escenario
t = T["TIR"]; fig, ax = plt.subplots(figsize=(7.2, 3.0))
ax.barh(range(len(t)), t["TIR real requerida"] * 100, color=C[0], height=0.6)
for i, v in enumerate(t["TIR real requerida"]): ax.annotate(f"{v*100:.2f}%", (v * 100, i), xytext=(3, 0), textcoords="offset points", va="center", fontsize=7.5, color=INK)
ax.set_yticks(range(len(t))); ax.set_yticklabels(t["Escenario"], fontsize=7.5); ax.invert_yaxis(); ax.set_xlabel("TIR real anual requerida (%)")
ax.set_title("Retorno real requerido para cumplir los tres objetivos", loc="left", color=INK, fontsize=10); save(fig, "f5_tir.png")

# 6. Robustez: Sharpe por variante
CORTO = {"BASE (vigente)": "Regla vigente", "BASE (vigente, 5 ETF)": "Regla vigente (5 ETF)", "Sin filtros absolutos (solo ranking)": "Sin filtros (solo ranking)", "Umbrales x2 (r6>10%, r12>20%)": "Umbrales x2", "Universo original 3 ETF (GLD, USO, DBA)": "Universo original 3 ETF", "Umbrales en cero (solo tendencia)": "Umbrales en cero", "Sin límite de volatilidad": "Sin límite de vol."}
rb = T["Robustez"]; fig, axs = plt.subplots(1, 3, figsize=(7.2, 3.0), sharex=False)
for ax, est in zip(axs, ["Momentum", "Low-Volatility", "Commodities"]):
    d = rb[rb.Estrategia == est].reset_index(drop=True)
    cols = [C[1] if v.startswith("BASE") else C[0] for v in d.Variante]
    ax.barh(range(len(d)), d.Sharpe, color=cols, height=0.6); ax.set_yticks(range(len(d))); ax.set_yticklabels([CORTO.get(v, v) for v in d.Variante], fontsize=6.5); ax.invert_yaxis()
    ax.set_title(est, fontsize=9, color=INK); ax.set_xlabel("Sharpe 2013-2026", fontsize=7.5)
fig.suptitle("Robustez: Sharpe de cada variante (naranja = regla vigente)", x=0.01, ha="left", fontsize=10, color=INK); save(fig, "f6_robustez.png")
print("figuras OK:", sorted(os.listdir(OUT)))

# 7. Abanico del patrimonio real (USD de hoy)
fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.3), sharey=False)
for ax, (k, tit) in zip(axs, [("Abanico_historico", "Retornos históricos 2013-2026"), ("Abanico_prospectivo", "Supuestos prospectivos")]):
    a = T[k]; y = a["Año"]
    ax.fill_between(y, a.P10 / 1e3, a.P90 / 1e3, color=C[0], alpha=0.15, lw=0, label="P10-P90")
    ax.fill_between(y, a.P25 / 1e3, a.P75 / 1e3, color=C[0], alpha=0.30, lw=0, label="P25-P75")
    ax.plot(y, a.P50 / 1e3, color=C[0], lw=2, label="Mediana")
    for x0, x1 in [(14, 20)]: ax.axvspan(x0, x1, color=GRID, alpha=0.6, lw=0)
    for x, t, hy in [(17, "Educación", 0.97), (25, "Villarrica", 0.89), (48.5, "Herencia", 0.97)]:
        if t != "Educación": ax.axvline(25 if t == "Villarrica" else 50, color=INK2, lw=0.6, ls=":")
        ax.annotate(t, (x, hy), xycoords=("data", "axes fraction"), ha="center", fontsize=7, color=INK2)
    ax.set_ylim(0, a.P90.max() / 1e3 * 1.12)
    ax.set_title(tit, fontsize=9, color=INK); ax.set_xlabel("Año")
axs[0].set_ylabel("Patrimonio (miles de USD de hoy)"); axs[1].legend(loc="upper left", fontsize=7, bbox_to_anchor=(0.0, 0.86))
fig.suptitle("Abanico del patrimonio de la cartera (20.000 escenarios)", x=0.01, ha="left", fontsize=10, color=INK); save(fig, "f7_abanico.png")

# 8. Peso vs contribución al riesgo
rc = T["Contribucion_riesgo"]; y = np.arange(len(rc)); h = 0.36
fig, ax = plt.subplots(figsize=(7.2, 3.0))
ax.barh(y - h / 2, rc["Peso"] * 100, height=h - 0.04, color=C[0], label="Peso en la cartera")
ax.barh(y + h / 2, rc["Contribución al riesgo (%)"] * 100, height=h - 0.04, color=C[1], label="Contribución al riesgo")
for i, (p, r) in enumerate(zip(rc["Peso"], rc["Contribución al riesgo (%)"])):
    ax.annotate(f"{p*100:.1f}%", (p * 100, i - h / 2), xytext=(3, 0), textcoords="offset points", va="center", fontsize=7, color=INK)
    ax.annotate(f"{r*100:.1f}%", (r * 100, i + h / 2), xytext=(3, 0), textcoords="offset points", va="center", fontsize=7, color=INK)
ax.set_yticks(y); ax.set_yticklabels([n.replace(" (", "\n(") for n in rc["Activo"]], fontsize=7.5); ax.invert_yaxis(); ax.set_xlabel("%")
ax.legend(loc="lower right"); ax.set_title("Peso frente a contribución al riesgo total de la cartera", loc="left", color=INK, fontsize=10); save(fig, "f8_riesgo.png")
print("figuras 7 y 8 OK")
