"""Construye modelo/Modelo_Nexum_v2.xlsx desde resultados/estado.pkl.

Convención de colores (estándar de modelación financiera):
  azul = dato de entrada editable · negro = fórmula · verde = vínculo a otra hoja · gris itálico = resultado de Python (valor)
"""
import os, datetime
import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.worksheet.formula import ArrayFormula
from config import *
import objetivos as O

S = pd.read_pickle(os.path.join(RESULTADOS, "estado.pkl")); T = S["T"]; df = S["df"]; bl = S["bl"]
wb = Workbook()
AR = "Arial"
F_T = Font(name=AR, size=14, bold=True, color="1F3A5F"); F_H = Font(name=AR, size=10, bold=True, color="FFFFFF")
F_IN = Font(name=AR, size=10, color="0000FF"); F_FX = Font(name=AR, size=10, color="000000"); F_LK = Font(name=AR, size=10, color="008000")
F_PY = Font(name=AR, size=10, italic=True, color="595959"); F_B = Font(name=AR, size=10, bold=True); F_N = Font(name=AR, size=10)
F_S = Font(name=AR, size=9, italic=True, color="595959"); F_SEC = Font(name=AR, size=11, bold=True, color="1F3A5F")
HDR = PatternFill("solid", fgColor="1F3A5F"); KEY = PatternFill("solid", fgColor="FFF2CC"); OKF = PatternFill("solid", fgColor="E2EFDA")
thin = Side(style="thin", color="D9D9D9"); BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
PCT, PCT1, NUM, NUM4, USD0 = "0.00%", "0.0%", "#,##0.00", "0.0000", '#,##0;(#,##0);"-"'

def hoja(nombre, titulo, sub=None):
    ws = wb.create_sheet(nombre); ws.sheet_view.showGridLines = False
    ws["B2"] = titulo; ws["B2"].font = F_T
    if sub: ws["B3"] = sub; ws["B3"].font = F_S
    ws.column_dimensions["A"].width = 2; return ws
def put(ws, ref, v, font=F_N, fmt=None, fill=None):
    c = ws[ref]; c.value = v; c.font = font; c.border = BOX
    if fmt: c.number_format = fmt
    if fill: c.fill = fill
    return c
def head(ws, row, col, labels):
    for j, h in enumerate(labels):
        c = ws.cell(row=row, column=col + j, value=h); c.font = F_H; c.fill = HDR; c.border = BOX; c.alignment = Alignment(wrap_text=True, vertical="center")
def sec(ws, ref, t): ws[ref] = t; ws[ref].font = F_SEC
def tabla(ws, row, col, d, fmts=None, font=F_PY):
    head(ws, row, col, list(d.columns))
    for i, r in enumerate(d.itertuples(index=False), 1):
        for j, v in enumerate(r):
            c = ws.cell(row=row + i, column=col + j, value=(None if (isinstance(v, float) and np.isnan(v)) else (float(v) if isinstance(v, (np.floating, np.integer)) else v)))
            c.font = font; c.border = BOX
            if fmts and isinstance(v, (int, float, np.floating)) and not isinstance(v, bool): c.number_format = fmts.get(d.columns[j], PCT)
    return row + len(d)
def anchos(ws, w):
    for k, v in w.items(): ws.column_dimensions[k].width = v

# ======================= 0. ÍNDICE =======================
ws = wb.active; ws.title = "00_Indice"; ws.sheet_view.showGridLines = False
ws["B2"] = "Nexum Financial Advisors — Modelo de inversión Familia Allende Cunich (v2)"; ws["B2"].font = F_T
ws["B3"] = f"Grupo 11 · ESF 2026-2 · Datos al 31-ago-2026 · Generado {datetime.date.today():%d-%m-%Y} con codigo/run_all.py + excel_modelo.py"; ws["B3"].font = F_S
sec(ws, "B5", "Flujo del modelo")
flujo = [("01_Supuestos", "Datos del cliente, objetivos, tipos de cambio, reglas de las estrategias y supuestos de mercado (todas las entradas)"),
         ("02_Objetivos_TIR", "Flujos años 0-50, TIR real requerida (fórmula IRR) y factibilidad"),
         ("03_Estrategias", "Reglas, resultados del backtest y comparación con su benchmark de cada estrategia activa"),
         ("04_Datos_Mensuales", "Retornos mensuales 2013-2026 de los 6 activos y del benchmark (salida de los backtests point-in-time)"),
         ("05_Markowitz", "Medias, volatilidades y covarianzas con fórmulas; cartera de máximo Sharpe histórico"),
         ("06_Black_Litterman", "Prior de paridad de riesgo, π implícito, vistas y μ posterior calculados con fórmulas matriciales"),
         ("07_Benchmark_Metricas", "Benchmark de política por sleeve, métricas de desempeño, tracking error ex-ante e IR"),
         ("08_Montecarlo", "Probabilidad de cumplir cada objetivo: USD y UF, histórico y prospectivo, Nexum vs AGF; palancas"),
         ("09_Validacion", "Impacto de correcciones, robustez de parámetros, walk-forward fuera de muestra y sesgos declarados"),
         ("10_Bitacora_Auditoria", "Errores encontrados en el modelo original y cómo se corrigieron")]
head(ws, 6, 2, ["Hoja", "Contenido"])
for i, (h, d) in enumerate(flujo, 7):
    c = ws.cell(row=i, column=2, value=h); c.hyperlink = f"#'{h}'!A1"; c.font = Font(name=AR, size=10, color="0563C1", underline="single"); c.border = BOX
    ws.cell(row=i, column=3, value=d).font = F_N; ws.cell(row=i, column=3).border = BOX
sec(ws, "B19", "Convención de colores")
for i, (t, f) in enumerate([("Azul: dato de entrada editable", F_IN), ("Negro: fórmula", F_FX), ("Verde: vínculo a otra hoja", F_LK),
                            ("Gris itálica: resultado calculado en Python (codigo/), reproducible con run_all.py", F_PY)], 20):
    ws.cell(row=i, column=2, value=t).font = f
sec(ws, "B25", "Resultado principal")
mc = T["Montecarlo"]; g = lambda c, e, m, k: mc[(mc.Cartera == c) & (mc.Escenario.str.startswith(e)) & (mc.Moneda == m)][k].iloc[0]
res = [("TIR real requerida (enunciado)", "='02_Objetivos_TIR'!D8", PCT),
       ("P(3 objetivos) histórico, USD", g("Nexum", "Hist", "USD", "P(3 objetivos)"), PCT1),
       ("P(3 objetivos) prospectivo, USD", g("Nexum", "Prosp", "USD", "P(3 objetivos)"), PCT1),
       ("P(Educación) en todos los escenarios", min(mc[mc.Cartera == "Nexum"]["P(Educación)"]), PCT1)]
for i, (k, v, f) in enumerate(res, 26):
    put(ws, f"B{i}", k, F_B); put(ws, f"C{i}", v, F_LK if isinstance(v, str) else F_PY, f, KEY)
anchos(ws, {"B": 34, "C": 110})

# ======================= 1. SUPUESTOS =======================
ws = hoja("01_Supuestos", "Supuestos y datos de entrada", "Fuente: enunciado 'Planificación Actividad de Graduación' y BCCh (11-ago-2026). Todo número del modelo nace aquí o en codigo/config.py.")
rows = [("Cliente y mercado", None, None, None),
        ("Capital inicial (USD)", CAPITAL, USD0, "Enunciado"), ("Reserva operativa + cambiaria", RESERVA, PCT1, "2% caja + 2% reserva; no se invierte"),
        ("Aporte anual (USD, abril)", APORTE, USD0, "Enunciado: hasta que Tomás cumpla 65"), ("N° de aportes", N_APORTES, "0", "46 → 65 años"),
        ("USD/CLP", USD_CLP, NUM, "BCCh 11-ago-2026"), ("UF/CLP", UF_CLP, NUM, "BCCh 11-ago-2026"), ("USD por UF", "=D10/D9", NUM4, "Fórmula"),
        ("Inflación EE.UU. (deflactor)", INFLACION_USD, PCT1, "Supuesto"),
        ("Objetivos", None, None, None),
        ("Arancel por hijo (CLP de hoy)", ARANCEL_CLP, "#,##0", "Enunciado"), ("Años de carrera", ANOS_CARRERA, "0", "Supuesto: 5 pagos anuales"),
        ("Pago anual por hijo (USD)", "=D14/D9/D15", USD0, "Fórmula"), ("Inicio Vicente (año)", INICIO_VICENTE, "0", "Enunciado ~14"),
        ("Inicio Emilia (año)", INICIO_EMILIA, "0", "Enunciado ~16"), ("Villarrica: desembolso (UF)", VILLARRICA_UF, "#,##0", "Enunciado; UF 15.000 restantes vienen de la venta de la casa (fuera de la cartera)"),
        ("Año Villarrica", ANO_VILLARRICA, "0", "Francisca cumple 65"), ("Herencia (USD de hoy)", HERENCIA_USD, USD0, "USD 250 mil por hijo"),
        ("Año herencia", ANO_HERENCIA, "0", "Francisca cumple 90"), ("Tasa real libre de riesgo", 0.025, PCT1, "Bono 10a EE.UU. ~5,2% − inflación implícita ~2,5%"),
        ("Asignación y gestión activa", None, None, None),
        ("Núcleo pasivo mínimo", NUCLEO_MIN, PCT1, "Política"), ("Núcleo pasivo máximo", NUCLEO_MAX, PCT1, "Política"),
        ("δ aversión al riesgo (BL)", BL_DELTA, NUM, "Black y Litterman (1992); ver A implícito en 06"), ("τ incertidumbre del prior (BL)", BL_TAU, NUM, "He y Litterman (1999)"),
        ("Alfa objetivo anual", ALFA_OBJETIVO, PCT1, "Presupuesto de riesgo activo"), ("Information ratio objetivo", IR_OBJETIVO, NUM, "Grinold y Kahn: 0,5 = bueno"),
        ("TE objetivo = alfa / IR", "=D29/D30", PCT1, "Fórmula"), ("TE máximo", TE_MAX, PCT1, "Alfa 2% con IR 0,5"),
        ("Costo de transacción por lado", COSTO_POR_LADO, PCT, "Sobre el monto transado")]
head(ws, 5, 2, ["Parámetro", "", "Valor", "Fuente / nota"]); r0 = 6
for i, (k, v, f, n) in enumerate(rows):
    r = r0 + i
    if v is None: sec(ws, f"B{r}", k); continue
    put(ws, f"B{r}", k); put(ws, f"D{r}", v, F_FX if isinstance(v, str) else F_IN, f); put(ws, f"E{r}", n, F_S)
anchos(ws, {"B": 36, "C": 2, "D": 16, "E": 80})
# referencias usadas por otras hojas
REF = {"cap": "'01_Supuestos'!$D$7", "res": "'01_Supuestos'!$D$8", "ap": "'01_Supuestos'!$D$9", "nap": "'01_Supuestos'!$D$10",
       "usdclp": "'01_Supuestos'!$D$11", "usduf": "'01_Supuestos'!$D$13", "pago": "'01_Supuestos'!$D$18", "carr": "'01_Supuestos'!$D$17",
       "iv": "'01_Supuestos'!$D$19", "ie": "'01_Supuestos'!$D$20", "vil": "'01_Supuestos'!$D$21", "avil": "'01_Supuestos'!$D$22",
       "her": "'01_Supuestos'!$D$23", "aher": "'01_Supuestos'!$D$24", "rf": "'01_Supuestos'!$D$25"}
# corregir referencias exactas según filas reales
lab2row = {k: r0 + i for i, (k, v, f, n) in enumerate(rows) if v is not None}
REF = {"cap": f"'01_Supuestos'!$D${lab2row['Capital inicial (USD)']}", "ap": f"'01_Supuestos'!$D${lab2row['Aporte anual (USD, abril)']}",
       "nap": f"'01_Supuestos'!$D${lab2row['N° de aportes']}", "usduf": f"'01_Supuestos'!$D${lab2row['USD por UF']}",
       "pago": f"'01_Supuestos'!$D${lab2row['Pago anual por hijo (USD)']}", "carr": f"'01_Supuestos'!$D${lab2row['Años de carrera']}",
       "iv": f"'01_Supuestos'!$D${lab2row['Inicio Vicente (año)']}", "ie": f"'01_Supuestos'!$D${lab2row['Inicio Emilia (año)']}",
       "vil": f"'01_Supuestos'!$D${lab2row['Villarrica: desembolso (UF)']}", "avil": f"'01_Supuestos'!$D${lab2row['Año Villarrica']}",
       "her": f"'01_Supuestos'!$D${lab2row['Herencia (USD de hoy)']}", "aher": f"'01_Supuestos'!$D${lab2row['Año herencia']}",
       "rf": f"'01_Supuestos'!$D${lab2row['Tasa real libre de riesgo']}", "delta": f"'01_Supuestos'!$D${lab2row['δ aversión al riesgo (BL)']}",
       "tau": f"'01_Supuestos'!$D${lab2row['τ incertidumbre del prior (BL)']}"}
# fórmulas internas de la hoja con filas reales
ws[f"D{lab2row['USD por UF']}"] = f"=D{lab2row['UF/CLP']}/D{lab2row['USD/CLP']}"
ws[f"D{lab2row['Pago anual por hijo (USD)']}"] = f"=D{lab2row['Arancel por hijo (CLP de hoy)']}/D{lab2row['USD/CLP']}/D{lab2row['Años de carrera']}"
ws[f"D{lab2row['TE objetivo = alfa / IR']}"] = f"=D{lab2row['Alfa objetivo anual']}/D{lab2row['Information ratio objetivo']}"
r = r0 + len(rows) + 1; sec(ws, f"B{r}", "Reglas de las estrategias activas")
reglas = pd.DataFrame([
 ["Momentum en acciones", "Universo", "S&P 500 point-in-time"], ["", "Filtros", "r3m > 0%, r6m > 5%, r12m > 10%, precio > media 200d, liquidez ≥ USD 5M/día, Sharpe 12m ≥ 0,5 (vol. 12 meses)"],
 ["", "Ranking", "50% percentil r6m + 50% percentil r12m"], ["", "Cartera", "Top 10, peso igual, máx. 25% por sector GICS; mensual"],
 ["Low-Volatility", "Universo", "S&P 500 point-in-time; precio ≥ USD 5; liquidez ≥ USD 5M/día"], ["", "Ranking", "Menor volatilidad realizada 12 meses"],
 ["", "Cartera", "Top 10, peso igual, máx. 25% por sector GICS; mensual"],
 ["Momentum en commodities", "Universo", "GLD, USO, DBA, SLV, CPER"], ["", "Filtros", "r3m > 5%, r6m > 8%, r12m > 10%, precio > media 200d, vol. 12m < 50%"],
 ["", "Cartera", "Todos los que califican, peso igual; sin señal → T-Bills; mensual"],
 ["Comunes", "Ejecución", "Señal al cierre del mes t, retorno desde t+1 (sin anticipación); costo 0,1% por lado"]], columns=["Estrategia", "Elemento", "Regla"])
tabla(ws, r + 1, 2, reglas, font=F_N)
r = r + len(reglas) + 3; sec(ws, f"B{r}", "Supuestos de mercado prospectivos (retornos reales anuales)")
tabla(ws, r + 1, 2, T["Supuestos_mercado"], {"Retorno real anual supuesto": PCT1}, font=F_IN)

# ======================= 2. OBJETIVOS Y TIR =======================
ws = hoja("02_Objetivos_TIR", "Objetivos, flujos y TIR real requerida", "USD reales de hoy. Entradas positivas, desembolsos negativos. Fórmulas vinculadas a 01_Supuestos.")
put(ws, "B5", "Indicador", F_B); put(ws, "D5", "Valor", F_B)
put(ws, "B6", "VP recursos a tasa libre de riesgo"); put(ws, "D6", "=NPV(" + REF["rf"] + ",E14:E63)+E13", F_FX, USD0)
put(ws, "B7", "VP objetivos a tasa libre de riesgo"); put(ws, "D7", "=-(NPV(" + REF["rf"] + ",J14:J63)+J13)", F_FX, USD0)
put(ws, "B8", "TIR real requerida (IRR de los flujos netos)", F_B); put(ws, "D8", "=IRR(K13:K63,0.04)", F_FX, PCT, KEY)
put(ws, "B9", "Cobertura (recursos / objetivos)"); put(ws, "D9", "=D6/D7", F_FX, "0.00x", KEY)
head(ws, 12, 2, ["Año", "Capital", "Aporte", "Educación Vicente", "Educación Emilia", "Villarrica", "Herencia", "Total salidas", "Flujo neto"])
ws.cell(row=12, column=5).value = "Entradas"
head(ws, 12, 2, ["Año", "Capital", "Aporte", "Entradas", "Educ. Vicente", "Educ. Emilia", "Villarrica", "Herencia", "Salidas", "Flujo neto"])
for t in range(51):
    r = 13 + t; put(ws, f"B{r}", t, F_N, "0")
    put(ws, f"C{r}", f"=IF(B{r}=0,{REF['cap']},0)", F_FX, USD0)
    put(ws, f"D{r}", f"=IF(AND(B{r}>=1,B{r}<={REF['nap']}),{REF['ap']},0)", F_FX, USD0)
    put(ws, f"E{r}", f"=C{r}+D{r}", F_FX, USD0)
    put(ws, f"F{r}", f"=IF(AND(B{r}>={REF['iv']},B{r}<{REF['iv']}+{REF['carr']}),-{REF['pago']},0)", F_FX, USD0)
    put(ws, f"G{r}", f"=IF(AND(B{r}>={REF['ie']},B{r}<{REF['ie']}+{REF['carr']}),-{REF['pago']},0)", F_FX, USD0)
    put(ws, f"H{r}", f"=IF(B{r}={REF['avil']},-{REF['vil']}*{REF['usduf']},0)", F_FX, USD0)
    put(ws, f"I{r}", f"=IF(B{r}={REF['aher']},-{REF['her']},0)", F_FX, USD0)
    put(ws, f"J{r}", f"=SUM(F{r}:I{r})", F_FX, USD0); put(ws, f"K{r}", f"=E{r}+J{r}", F_FX, USD0)
put(ws, "M5", "Escenarios de TIR (Python, objetivos.py)", F_SEC)
tabla(ws, 6, 13, T["TIR"], {"TIR real requerida": PCT})
put(ws, "M18", "Plan de desembolsos", F_SEC); tabla(ws, 19, 13, T["Plan_desembolsos"], {"Año": "0", "USD reales": USD0, "UF": "#,##0.0", "CLP de hoy": "#,##0"})
put(ws, "M33", "Nota: no se usa la venta de la casa de Santiago más allá de las UF 15.000 que el enunciado asigna a Villarrica.", F_S)
anchos(ws, {"B": 40, "C": 11, "D": 13, "E": 11, "F": 12, "G": 12, "H": 12, "I": 12, "J": 12, "K": 12, "M": 52, "N": 16, "O": 14, "P": 12, "Q": 16})

# ======================= 3. ESTRATEGIAS =======================
ws = hoja("03_Estrategias", "Estrategias activas: resultados y comparación con su benchmark", "Backtests point-in-time (codigo/estrategias.py). Métricas vs T-Bills (BIL).")
e = T["Estrategias"].copy()
cols = ["Estrategia", "Benchmark", "CAGR", "Volatilidad", "Sharpe", "Sortino", "Beta", "Alfa CAPM", "Máx. caída", "VaR 95% mensual", "CVaR 95% mensual", "Tracking error", "Information ratio"]
e = e[[c for c in cols if c in e.columns]]
tabla(ws, 5, 2, e, {c: (NUM if c in ("Sharpe", "Sortino", "Beta", "Information ratio") else PCT) for c in e.columns})
anchos(ws, {"B": 40, "C": 14, **{L(i): 12 for i in range(4, 16)}})

# ======================= 4. DATOS =======================
ws = hoja("04_Datos_Mensuales", "Retornos mensuales nominales en USD (ene-2013 a ago-2026, 164 meses)", "Fuente: backtests point-in-time (estrategias activas) y Yahoo Finance ajustado por dividendos (ETF).")
data = df.copy(); bser = S["bser"].add_prefix("BM_")
allc = pd.concat([data, bser], axis=1)
head(ws, 5, 2, ["Fecha"] + list(allc.columns))
for i, (d, row) in enumerate(allc.iterrows(), 6):
    ws.cell(row=i, column=2, value=d.date()).number_format = "yyyy-mm"
    for j, v in enumerate(row, 3):
        c = ws.cell(row=i, column=j, value=None if pd.isna(v) else float(v)); c.number_format = PCT; c.font = F_PY
NR = 5 + len(allc); RNG = {a: f"'04_Datos_Mensuales'!${L(3 + k)}$6:${L(3 + k)}${NR}" for k, a in enumerate(ACTIVOS)}
anchos(ws, {"B": 11, **{L(i): 11 for i in range(3, 3 + allc.shape[1])}})

# ======================= 5. MARKOWITZ =======================
ws = hoja("05_Markowitz", "Markowitz: estadísticos con fórmulas y cartera de máximo Sharpe histórico", "Referencia: optimizar con medias históricas sobreajusta (ver walk-forward en 09). La recomendación es Black-Litterman (06).")
head(ws, 5, 2, ["Activo", "Retorno anual", "Volatilidad anual", "Peso Markowitz (máx. Sharpe, SLSQP)", "Peso aprobado (BL)"])
mk = S["mk"]
for k, a in enumerate(ACTIVOS):
    r = 6 + k; put(ws, f"B{r}", NOMBRES[a]); put(ws, f"C{r}", f"=AVERAGE({RNG[a]})*12", F_FX, PCT); put(ws, f"D{r}", f"=_xlfn.STDEV.S({RNG[a]})*SQRT(12)", F_FX, PCT)
    put(ws, f"E{r}", float(mk["w"][a]), F_PY, PCT); put(ws, f"F{r}", PESOS_APROBADOS[a], F_IN, PCT)
put(ws, "B13", "Matriz de covarianza anual (fórmulas COVARIANCE.S)", F_SEC)
head(ws, 14, 3, [NOMBRES[a][:22] for a in ACTIVOS])
for i, a in enumerate(ACTIVOS):
    put(ws, f"B{15 + i}", NOMBRES[a])
    for j, b in enumerate(ACTIVOS): put(ws, f"{L(3 + j)}{15 + i}", f"=_xlfn.COVARIANCE.S({RNG[a]},{RNG[b]})*12", F_FX, "0.00000")
COV = "'05_Markowitz'!$C$15:$H$20"
for lab, col, r in [("Markowitz", "E", 23), ("Pesos aprobados", "F", 27)]:
    put(ws, f"B{r}", f"Cartera {lab}", F_SEC)
    put(ws, f"B{r+1}", "Retorno anual"); ws[f"C{r+1}"] = ArrayFormula(f"C{r+1}", f"=SUMPRODUCT({col}6:{col}11,C6:C11)"); ws[f"C{r+1}"].number_format = PCT
    put(ws, f"B{r+2}", "Volatilidad anual"); ws[f"C{r+2}"] = ArrayFormula(f"C{r+2}", f"=SQRT(MMULT(TRANSPOSE({col}6:{col}11),MMULT(C15:H20,{col}6:{col}11)))"); ws[f"C{r+2}"].number_format = PCT
    put(ws, f"B{r+3}", "Sharpe (rf = 0, misma convención del optimizador)"); put(ws, f"C{r+3}", f"=C{r+1}/C{r+2}", F_FX, NUM)
put(ws, "B32", "Restricciones: suma = 100%; núcleo (SPY+TLH+VCLT) entre 60% y 70%; TLH y VCLT ≥ 8%; sin ventas cortas.", F_S)
put(ws, "B33", "Chequeo núcleo Markowitz"); put(ws, "C33", "=IF(AND(SUM(E6:E8)>=0.6-1E-6,SUM(E6:E8)<=0.7+1E-6,ABS(SUM(E6:E11)-1)<1E-6),\"OK\",\"REVISAR\")", F_FX)
anchos(ws, {"B": 40, **{L(i): 16 for i in range(3, 9)}})

# ======================= 6. BLACK-LITTERMAN =======================
ws = hoja("06_Black_Litterman", "Black-Litterman: equilibrio + vistas → retornos esperados y cartera recomendada", "π = δ·Σ·w_eq ; μ_BL = [(τΣ)⁻¹ + PᵀΩ⁻¹P]⁻¹ [(τΣ)⁻¹π + PᵀΩ⁻¹Q] ; Ω = diag(P·τΣ·Pᵀ). Fórmulas matriciales vivas.")
head(ws, 5, 2, ["Activo", "Volatilidad", "Prior w_eq (1/vol normalizado)", "π implícito", "μ Black-Litterman", "Peso BL recalibrado (SLSQP)", "Peso aprobado", "Diferencia (pp)"])
for k, a in enumerate(ACTIVOS):
    r = 6 + k; put(ws, f"B{r}", NOMBRES[a]); put(ws, f"C{r}", f"='05_Markowitz'!D{6 + k}", F_LK, PCT)
    put(ws, f"D{r}", f"=(1/C{r})/SUMPRODUCT(1/$C$6:$C$11)", F_FX, PCT)
    put(ws, f"G{r}", float(bl["w"][a]), F_PY, PCT); put(ws, f"H{r}", f"='05_Markowitz'!F{6 + k}", F_LK, PCT); put(ws, f"I{r}", f"=(G{r}-H{r})*100", F_FX, NUM)
ws["E6"] = ArrayFormula("E6:E11", f"={REF['delta']}*MMULT({COV},D6:D11)")
for r in range(6, 12): ws[f"E{r}"].number_format = PCT; ws[f"E{r}"].font = F_FX; ws[f"E{r}"].border = BOX
put(ws, "B13", "Vistas del inversionista", F_SEC)
head(ws, 14, 2, ["Vista", "Tipo"] + [a for a in ACTIVOS] + ["Q (retorno)", "Fundamento"])
for i, (tipo, vec, q, why) in enumerate(BL_VISTAS):
    r = 15 + i; put(ws, f"B{r}", f"Vista {i+1}"); put(ws, f"C{r}", tipo)
    for j, a in enumerate(ACTIVOS): put(ws, f"{L(4 + j)}{r}", vec.get(a, 0.0), F_IN, "0")
    put(ws, f"J{r}", q, F_IN, PCT1); put(ws, f"K{r}", why, F_S)
put(ws, "B18", "τΣ"); ws["C19"] = ArrayFormula("C19:H24", f"={REF['tau']}*{COV}")
put(ws, "B26", "Ω (diagonal)"); ws["C27"] = ArrayFormula("C27:D28", "=MMULT(D15:I16,MMULT(C19:H24,TRANSPOSE(D15:I16)))*{1,0;0,1}")
put(ws, "B30", "μ_BL calculado"); ws["C31"] = ArrayFormula("C31:C36",
    "=MMULT(MINVERSE(MINVERSE(C19:H24)+MMULT(TRANSPOSE(D15:I16),MMULT(MINVERSE(C27:D28),D15:I16))),"
    "MMULT(MINVERSE(C19:H24),E6:E11)+MMULT(TRANSPOSE(D15:I16),MMULT(MINVERSE(C27:D28),J15:J16)))")
for r in range(19, 25):
    for cc in "CDEFGH": ws[f"{cc}{r}"].number_format = "0.000000"
for r in range(31, 37): ws[f"C{r}"].number_format = PCT; ws[f"B{r}"] = NOMBRES[ACTIVOS[r - 31]]
for k in range(6): ws[f"F{6 + k}"] = f"=C{31 + k}"; ws[f"F{6 + k}"].number_format = PCT; ws[f"F{6 + k}"].border = BOX
put(ws, "B39", "Cartera recomendada (pesos aprobados)", F_SEC)
put(ws, "B40", "Retorno esperado (μ_BL)"); ws["C40"] = ArrayFormula("C40", "=SUMPRODUCT(H6:H11,F6:F11)"); ws["C40"].number_format = PCT
put(ws, "B41", "Volatilidad"); put(ws, "C41", "='05_Markowitz'!C29", F_LK, PCT)
put(ws, "B42", "Sharpe sobre μ_BL"); put(ws, "C42", "=C40/C41", F_FX, NUM)
put(ws, "B43", "Núcleo pasivo (SPY+TLH+VCLT)"); put(ws, "C43", "=SUM(H6:H8)", F_FX, PCT1)
put(ws, "B44", "Chequeo: Σ pesos = 100%"); put(ws, "C44", "=IF(ABS(SUM(H6:H11)-1)<0.0005,\"OK\",\"REVISAR\")", F_FX)
put(ws, "B46", "Lectura: los pesos recalibrados con los datos corregidos difieren en menos de 0,7 pp de los aprobados (dentro de la banda de rebalanceo de ±2 pp): se mantienen los pesos aprobados, que ya están implementados.", F_S)
av = T["Aversion_riesgo"]; put(ws, "B48", "Aversión al riesgo", F_SEC); tabla(ws, 49, 2, av, {"Valor": NUM})
anchos(ws, {"B": 40, **{L(i): 15 for i in range(3, 12)}, "K": 50})

# ======================= 7. BENCHMARK Y MÉTRICAS =======================
ws = hoja("07_Benchmark_Metricas", "Benchmark de política, métricas y tracking error", "Benchmark compuesto en USD, ponderado por los pesos aprobados; cada sleeve contra un índice invertible de su mismo universo.")
bm = pd.DataFrame([{"Sleeve": NOMBRES[a], "Peso": PESOS_APROBADOS[a], "Benchmark": {"SPY": "S&P 500 (SPY)", "TLH": "ICE U.S. Treasury 10-20 Year (TLH)", "VCLT": "Bloomberg U.S. Long Corporate (VCLT)",
       "QMOM": "Alpha Architect U.S. Quantitative Momentum (QMOM)", "SPLV": "S&P 500 Low Volatility Index (SPLV)", "MEZCLA_CMD": "Mezcla igual ponderada GLD/USO/DBA/SLV/CPER"}[BENCH[a]]} for a in ACTIVOS])
tabla(ws, 5, 2, bm, {"Peso": PCT}, font=F_N)
m = T["Metricas"]; keep = ["Período", "Serie", "CAGR", "Volatilidad", "Sharpe", "Sortino", "Treynor", "Beta", "Alfa CAPM", "Máx. caída", "Calmar", "VaR 95% mensual", "CVaR 95% mensual", "Tracking error", "Information ratio"]
put(ws, "B13", "Métricas (USD nominal; Sharpe vs T-Bills)", F_SEC)
tabla(ws, 14, 2, m[[k for k in keep if k in m.columns]], {k: (NUM if k in ("Sharpe", "Sortino", "Treynor", "Beta", "Calmar", "Information ratio") else PCT) for k in keep})
put(ws, "B24", "Tracking error: derivación y situación actual", F_SEC); tabla(ws, 25, 2, T["Tracking_error"], {"Valor": PCT})
anchos(ws, {"B": 44, "C": 30, "D": 44, **{L(i): 12 for i in range(5, 17)}})

# ======================= 8. MONTECARLO =======================
ws = hoja("08_Montecarlo", "Montecarlo: probabilidad de cumplir los objetivos (20.000 escenarios, 50 años)",
          "Bootstrap mensual. Prospectivo: misma volatilidad y correlaciones, medias ajustadas a supuestos de mercado. UF: tipo de cambio real sin tendencia, con su volatilidad y correlación histórica.")
mcv = T["Montecarlo"]; tabla(ws, 5, 2, mcv, {c: (USD0 if "Saldo" in c else PCT1) for c in mcv.columns})
put(ws, "B16", "Palancas acordables con el cliente (escenario prospectivo, USD)", F_SEC); tabla(ws, 17, 2, T["Palancas"], {c: PCT1 for c in T["Palancas"].columns})
anchos(ws, {"B": 14, "C": 22, "D": 9, **{L(i): 13 for i in range(5, 20)}})

# ======================= 9. VALIDACIÓN =======================
ws = hoja("09_Validacion", "Validación: correcciones, robustez y prueba fuera de muestra")
put(ws, "B5", "Impacto de las correcciones sobre el modelo original", F_SEC)
ic = T["Impacto_correcciones"]; tabla(ws, 6, 2, ic, {c: ("0" if c == "Meses" else (NUM if "Sharpe" in c else PCT)) for c in ic.columns})
put(ws, "B12", "Robustez de parámetros (un cambio a la vez; backtest completo)", F_SEC)
rb = T["Robustez"]; tabla(ws, 13, 2, rb, {c: (NUM if "Sharpe" in c else PCT) for c in rb.columns})
r = 14 + len(rb) + 1; put(ws, f"B{r}", "Walk-forward: calibrar con 2013-2019, evaluar 2020-2026", F_SEC)
wf = T["Walk_forward"]; tabla(ws, r + 1, 2, wf, {c: (NUM if c == "Sharpe" else PCT) for c in wf.columns})
r = r + len(wf) + 3; put(ws, f"B{r}", "Sesgos y limitaciones declarados", F_SEC)
ses = ["Supervivencia: controlado con membresía histórica del S&P 500 (point-in-time).",
       "Anticipación: señal al cierre de t, retorno desde t+1. Limitación: clasificación GICS actual (no histórica) en el límite sectorial; afecta sobre todo antes de 2016 y a ~3% de posiciones sin clasificar.",
       "Datos faltantes: un precio faltante en el mes se trata como 0% en esa posición (antes eliminaba el mes completo en Low-Vol).",
       "Selección del universo de commodities: SLV y CPER se agregaron mirando el backtest (sesgo de selección). Se reporta el universo original de 3 ETF como control.",
       "Costos: convención de un lado (0,1% sobre ½·Σ|Δw|); la sensibilidad con ambos lados se muestra arriba.",
       "Montecarlo: bootstrap independiente (no captura regímenes ni autocorrelación); supuestos prospectivos propios, no pronósticos."]
for i, t in enumerate(ses, r + 1): put(ws, f"B{i}", "• " + t, F_N)
anchos(ws, {"B": 46, "C": 40, **{L(i): 12 for i in range(4, 20)}})

# ======================= 10. BITÁCORA =======================
ws = hoja("10_Bitacora_Auditoria", "Bitácora de auditoría del modelo original (Modelo_Nexum_Final.xlsx)")
bit = pd.DataFrame([
 ["Alta", "Fórmulas sin valores guardados (archivo escrito por código, nunca recalculado)", "Este archivo se recalcula y guarda en Excel antes de entregarse"],
 ["Alta", "Mezcla de dos arquitecturas: hojas y textos del diseño anterior con calce LDI de Educación (03, 05, partes de 02, 04, 09)", "Se eliminan; el modelo describe solo la cartera única"],
 ["Alta", "Referencias a 'BAB_EQ' (Betting Against Beta) en 05_Datos_Historicos", "Eliminadas; la estrategia se denomina Low-Volatility"],
 ["Alta", "Low-Vol devolvía NaN en jul-2018 y dic-2018; el modelo eliminó esos meses de las 6 series (162 en vez de 164 meses)", "Dato faltante = 0% en esa posición; ventana completa de 164 meses"],
 ["Alta", "Filtro 'Sharpe 12m' de Momentum calculado con volatilidad de 1 mes en el backtest, pero con 12 meses en la operación (Senales_Hoy.py)", "Backtest con volatilidad de 12 meses (regla documentada = regla operada)"],
 ["Media", "Black-Litterman: columna π de la sección 5 desplazada una fila (=D32 en vez de =D31)", "π y μ_BL se calculan con fórmulas matriciales vivas"],
 ["Media", "μ_BL y pesos pegados como valores, no auditables en el Excel", "μ_BL con MMULT/MINVERSE; pesos de SLSQP marcados como resultado de Python"],
 ["Media", "Benchmarks inconsistentes entre hojas 04 y 08 (BCOM, S&P Low Vol, S&P Momentum vs mezcla, SPY, QMOM)", "Un solo benchmark por sleeve, invertible y del mismo universo (hoja 07)"],
 ["Media", "Universo de commodities ampliado de 3 a 5 ETF eligiendo la combinación que más subía el Sharpe del backtest", "Declarado como sesgo de selección; control con universo de 3 ETF en 09"],
 ["Baja", "Métricas distintas para la misma estrategia según la hoja (p. ej. Sharpe Low-Vol 0,993 vs 0,81)", "Una sola convención: ventana 2013-2026 (o 2016-2026 vs benchmark), exceso sobre T-Bills"],
 ["Baja", "Falta el límite sectorial de 25% en la ficha de Momentum (sí estaba en el código)", "Incluido en 01_Supuestos"],
 ["Baja", "Notas 'PENDIENTE', 'Borrador' y 'Provisional' visibles", "Eliminadas"]], columns=["Gravedad", "Hallazgo", "Corrección en v2"])
tabla(ws, 5, 2, bit, font=F_N); anchos(ws, {"B": 10, "C": 95, "D": 75})
for row in ws.iter_rows(min_row=6, max_row=5 + len(bit)):
    for c in row: c.alignment = Alignment(wrap_text=True, vertical="top")

out = os.path.join(MODELO, "Modelo_Nexum_v2.xlsx"); os.makedirs(MODELO, exist_ok=True)
wb.calculation.fullCalcOnLoad = True; wb.save(out); print("OK", out)
