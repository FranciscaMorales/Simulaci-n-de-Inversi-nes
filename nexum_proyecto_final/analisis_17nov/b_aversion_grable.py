"""17-nov · Aversión al riesgo (A) despejada de las respuestas de apuestas del cuestionario de Grable y Lytton (1999).

Idea: cada pregunta con montos y probabilidades es una elección entre loterías. Si el cliente eligió X sobre Y,
su utilidad cumple U(X) >= U(Y). Con utilidad de aversión absoluta constante (CARA), u(w) = -exp(-a·w), cada
elección da una cota para a. La aversión relativa (la A de Bodie-Kane-Marcus, U = E(r) - ½·A·σ²) es A = a × riqueza.
Respuestas (Anexo 1): P2 eligió "50% de ganar 5.000" (vs 1.000 seguro, 25% de 10.000, 5% de 100.000);
P8 eligió "+2.600 / -800" (vs +200/0, +800/-200, +4.800/-2.400; 50/50); P9 eligió 500 seguro (vs 50% de 1.000);
P10 eligió "50% de perder 1.000" (vs perder 500 seguro).
"""
import numpy as np, pandas as pd
from scipy.optimize import brentq

def ce(pagos, probs, a):                       # equivalente cierto con CARA
    pagos, probs = np.array(pagos, float), np.array(probs, float)
    if a < 1e-12: return (pagos * probs).sum()
    m = pagos.min(); return m - np.log((probs * np.exp(-a * (pagos - m))).sum()) / a

P2 = {"a": ([1000], [1]), "b": ([5000, 0], [.5, .5]), "c": ([10000, 0], [.25, .75]), "d": ([100000, 0], [.05, .95])}
P8 = {"a": ([200, 0], [.5, .5]), "b": ([800, -200], [.5, .5]), "c": ([2600, -800], [.5, .5]), "d": ([4800, -2400], [.5, .5])}

def rango(preg, elegida):
    """Valores de a (por dólar) en que la opción elegida es la mejor."""
    grid = np.logspace(-7, -2, 4000)
    ok = [a for a in grid if all(ce(*preg[elegida], a) >= ce(*preg[o], a) - 1e-9 for o in preg)]
    return (min(ok), max(ok)) if ok else (np.nan, np.nan)

r2, r8 = rango(P2, "b"), rango(P8, "c")
lo, hi = max(r2[0], r8[0]), min(r2[1], r8[1])
filas = [{"Pregunta": "P2 programa de TV", "a mín (1/USD)": r2[0], "a máx (1/USD)": r2[1]},
         {"Pregunta": "P8 mejor/peor caso", "a mín (1/USD)": r8[0], "a máx (1/USD)": r8[1]},
         {"Pregunta": "Ambas a la vez", "a mín (1/USD)": lo, "a máx (1/USD)": hi}]
t = pd.DataFrame(filas)
# Riqueza de referencia: la cartera (USD 150.000). A = a × W
W = 150_000
t["A mín (W=150k)"] = t["a mín (1/USD)"] * W; t["A máx (W=150k)"] = t["a máx (1/USD)"] * W
print(t.to_string(index=False))
print("P9 (500 seguro vs 50% de 1.000, mismo valor esperado): consistente con cualquier A > 0.")
print("P10 (prefiere arriesgar una pérdida de 1.000 a perder 500 seguro): busca riesgo en pérdidas;"
      " ninguna A > 0 lo explica -> efecto de encuadre (Kahneman y Tversky, 1979).")
pd.to_pickle({"tabla": t, "A_rango": (lo * W, hi * W)}, "/tmp/claude-0/-home-user-Simulaci-n-de-Inversi-nes/ba76a289-564e-50db-8af1-18eaab1db098/scratchpad/run12/resultados/b_aversion.pkl")
