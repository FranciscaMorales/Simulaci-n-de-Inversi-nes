"""Genera informe/Informe_Final_Nexum.docx con cifras tomadas de resultados/estado.pkl."""
import os
import pandas as pd
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from config import *

S = pd.read_pickle(os.path.join(RESULTADOS, "estado.pkl")); T = S["T"]; FIG = os.path.join(BASE, "informe", "figuras")
AD = pd.read_pickle(os.path.join(RESULTADOS, "adicional.pkl"))   # codigo/analisis_adicional.py: benchmark por clase, forward y rebalanceo
AZ = RGBColor(0x1F, 0x3A, 0x5F)
d = Document()
for s in d.sections: s.left_margin = s.right_margin = Cm(2.3); s.top_margin = s.bottom_margin = Cm(2.0)
st = d.styles["Normal"]; st.font.name = "Arial"; st.font.size = Pt(10); st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
st.paragraph_format.space_after = Pt(5); st.paragraph_format.line_spacing = 1.12
for h, sz in [("Heading 1", 15), ("Heading 2", 12), ("Heading 3", 10.5)]:
    x = d.styles[h]; x.font.name = "Arial"; x.font.size = Pt(sz); x.font.color.rgb = AZ; x.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
p_ = lambda v, n=1: "—" if pd.isna(v) else (f"{v*100:.{n}f}%").replace(".", ",")
n_ = lambda v, n=2: "—" if pd.isna(v) else (f"{v:,.{n}f}").replace(",", "X").replace(".", ",").replace("X", ".")
u_ = lambda v: "USD " + n_(v, 0)
def H(t, l=1): d.add_heading(t, level=l)
def P(t, b=None, it=False, sz=None, al=None):
    p = d.add_paragraph()
    if b: r = p.add_run(b); r.bold = True
    r = p.add_run(t); r.italic = it
    if sz: r.font.size = Pt(sz)
    if al: p.alignment = al
    return p
def B(items):
    for x in items:
        p = d.add_paragraph(style="List Bullet")
        if isinstance(x, tuple): r = p.add_run(x[0]); r.bold = True; p.add_run(x[1])
        else: p.add_run(x)
def shade(c, col):
    pr = c._tc.get_or_add_tcPr(); sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), col); pr.append(sh)
def TB(hdr, rows, w=None, sz=8.5, nota=None):
    t = d.add_table(rows=1, cols=len(hdr)); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(hdr):
        c = t.rows[0].cells[i]; c.text = ""; r = c.paragraphs[0].add_run(str(h)); r.bold = True; r.font.size = Pt(sz); r.font.color.rgb = RGBColor(255, 255, 255); shade(c, "1F3A5F")
    for k, row in enumerate(rows):
        cs = t.add_row().cells
        for i, v in enumerate(row):
            cs[i].text = ""; r = cs[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(sz)
            if k % 2: shade(cs[i], "F2F5F9")
    if w:
        for row in t.rows:
            for i, x in enumerate(w): row.cells[i].width = Cm(x)
    if nota: P(nota, it=True, sz=8)
    else: d.add_paragraph()
def FIGURA(n, cap, w=16):
    d.add_picture(os.path.join(FIG, n), width=Cm(w)); d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER; P(cap, it=True, sz=8, al=WD_ALIGN_PARAGRAPH.CENTER)

mc = T["Montecarlo"]; g = lambda c, e, m, k: mc[(mc.Cartera == c) & mc.Escenario.str.startswith(e) & (mc.Moneda == m)][k].iloc[0]
fac = S["fac"]; met = T["Metricas"]; mt = lambda per, s, k: met[(met["Período"] == per) & (met.Serie == s)][k].iloc[0]
te = T["Tracking_error"].set_index("Concepto")["Valor"]; tir = T["TIR"].set_index("Escenario")["TIR real requerida"]
pal = T["Palancas"].set_index("Palanca (prospectivo, USD)"); ic = T["Impacto_correcciones"]; asg = T["Asignacion"]; av = T["Aversion_riesgo"]["Valor"].tolist()
wf = T["Walk_forward"]; wfv = lambda c, per: wf[(wf.Cartera == c) & wf["Período"].str.startswith(per)]["Sharpe"].iloc[0]
rb = T["Robustez"]; rbv = lambda e, v: rb[(rb.Estrategia == e) & rb.Variante.str.startswith(v)]["Sharpe"].iloc[0]
es = T["Estrategias"]; esv = lambda e, k: es[es.Estrategia == e][k].iloc[0]

# ================= PORTADA =================
P("Nexum Financial Advisors", al=WD_ALIGN_PARAGRAPH.CENTER).runs[0].font.size = Pt(22)
d.paragraphs[-1].runs[0].bold = True; d.paragraphs[-1].runs[0].font.color.rgb = AZ
P("Investment Policy Statement e Informe de Estrategia de Inversión", al=WD_ALIGN_PARAGRAPH.CENTER).runs[0].font.size = Pt(14)
P("Familia Allende Cunich · Mandato USD 150.000 + aportes anuales", al=WD_ALIGN_PARAGRAPH.CENTER)
P("Grupo 11 — M. José Iannello, Martín Lillo, Francisca Morales, Vicente Salah, Matías Torres", it=True, al=WD_ALIGN_PARAGRAPH.CENTER)
P("ESF 2026-2 · Universidad Adolfo Ibáñez · Datos de mercado al 31-ago-2026; implementación al 5-oct-2026", it=True, sz=9, al=WD_ALIGN_PARAGRAPH.CENTER)
P("Todas las cifras de este documento son reproducibles con codigo/run_all.py y coinciden con modelo/Modelo_Nexum_v2.xlsx.", it=True, sz=8.5, al=WD_ALIGN_PARAGRAPH.CENTER)
d.add_page_break()

# ================= 1. RESUMEN EJECUTIVO =================
H("1. Resumen ejecutivo")
P("¿Se cumplen los objetivos de la familia y con qué riesgo? ", b="La pregunta del cliente: ")
B([("Retorno requerido. ", f"Para financiar Educación, Villarrica y la herencia con USD 150.000 y 19 aportes de USD 10.000, la cartera debe rendir {p_(fac['TIR requerida'],2)} real anual (TIR de los flujos del enunciado). Con supuestos más exigentes y fieles al caso —aportes en USD nominales, arancel creciendo 2% real, 14 años efectivos de aportes— el requerimiento sube a {p_(tir.iloc[5],1)}."),
   ("Factibilidad. ", f"A la tasa real libre de riesgo (2,5%), los objetivos valen {u_(fac['VP objetivos'])} y los recursos {u_(fac['VP recursos (capital + aportes)'])}: cobertura de {n_(fac['Cobertura (recursos / objetivos)'],2)}x. El plan exige capturar prima por riesgo. Villarrica explica {p_(fac['Peso VP Villarrica'],0)} del valor presente de los objetivos."),
   ("Asignación. ", "Núcleo pasivo 69,4% (S&P 500 37,9%, Tesoro 10-20 años 16,9%, corporativos largos 14,6%) y satélite activo 30,6% (Low-Volatility 17,5%, Momentum en acciones 7,1%, Momentum en commodities 6,1%), obtenido con Black-Litterman. Renta variable efectiva 62%."),
   ("Probabilidad de éxito. ", f"Educación se cumple en ~100% de los escenarios simulados, en USD y en UF. Con retornos históricos 2013-2026, los tres objetivos se cumplen con {p_(g('Nexum','Hist','USD','P(3 objetivos)'))} ({p_(g('Nexum','Hist','UF','P(3 objetivos)'))} medido en UF). Con supuestos prospectivos prudentes —retorno real esperado {p_(g('Nexum','Prosp','USD','Retorno real anual'))}, prácticamente igual al requerido— la probabilidad conjunta es {p_(g('Nexum','Prosp','USD','P(3 objetivos)'))}."),
   ("Frente a la cartera actual de la AGF (85/15). ", f"La AGF rindió más en 2016-2026 ({p_(mt('2016-2026','Cartera actual AGF 85/15','CAGR'))} vs {p_(mt('2016-2026','Cartera Nexum','CAGR'))} anual) por su 76,5% en el S&P 500, con mayor volatilidad, caídas más profundas y ~26% de exposición a tecnología (el mismo riesgo del empleo de Tomás; Nexum ~14%). Hacia adelante, Nexum entrega mayor probabilidad de éxito ({p_(g('Nexum','Prosp','UF','P(3 objetivos)'))} vs {p_(g('AGF 85/15','Prosp','UF','P(3 objetivos)'))} en UF)."),
   ("Gestión activa. ", f"Tracking error ex-ante {p_(te.iloc[0])} (objetivo 3%, máximo 4%) e information ratio {n_(mt('2016-2026','Cartera Nexum','Information ratio'))} frente al benchmark de política en 2016-2026."),
   ("Riesgo cambiario. ", "El 28-sep-2026 se contrató un forward de venta de USD 104.000 a un año (~70% de la cartera), cerca de la cobertura que minimiza el riesgo medido en pesos: en la simulación, la volatilidad anual en pesos baja de {} a {}.".format(
       *[p_(AD["Forward_simulacion"].set_index(["Medido en", "Cartera"]).loc[("CLP (moneda de las metas)", c), "Volatilidad"]) for c in ["Sin cobertura", "Con el forward"]])),
   ("Recomendación. ", f"Mantener la asignación, proteger Educación como prioridad 1 y acordar con la familia el orden de ajuste si el mercado no entrega el retorno requerido: primero la herencia, luego Villarrica, nunca Educación. Reducir Villarrica 25% y la herencia a USD 250.000 eleva la probabilidad conjunta prospectiva de {p_(pal.loc['Base','P(3 objetivos)'])} a {p_(pal.loc['Ambas','P(3 objetivos)'])}.")])

# ================= 2. IPS =================
d.add_page_break(); H("2. Investment Policy Statement")
H("2.1 Propósito y alcance", 2)
P("Este IPS es el acuerdo entre Nexum Financial Advisors (el Asesor) y María Ignacia Cunich y Tomás Allende (el Cliente) para administrar USD 150.000 hoy invertidos en fondos mutuos de una AGF chilena, más aportes de USD 10.000 cada abril hasta que Tomás cumpla 65 años. Define objetivos, restricciones, asignación de activos, reglas de selección y rebalanceo, métricas de evaluación y la política de revisión. Toda decisión de inversión se toma dentro de este marco.")
H("2.2 Deberes y responsabilidades", 2)
P("El Asesor actúa como fiduciario, bajo el Código de Ética y los Estándares de Conducta Profesional del CFA Institute y la normativa de la CMF. Sus responsabilidades: recomendar una asignación coherente con el perfil, seleccionar los instrumentos, ejecutar y rebalancear, monitorear el desempeño contra el benchmark e informar al Cliente. El Cliente debe informar oportunamente cualquier cambio material (empleo, patrimonio, objetivos), lo que gatilla la revisión de este IPS.")
TB(["Control de cumplimiento (CMF / Ley 19.913)", "Meta medible"], [
    ["Conozca a su cliente: identidad, condición de Persona Expuesta Políticamente y perfil transaccional", "100% antes de operar"],
    ["Origen de fondos: acreditar que los USD 150.000 provienen de ahorro laboral en una AGF regulada; documentar cada aporte anual", "100% de los aportes"],
    ["Monitoreo de operaciones inusuales respecto del perfil (montos o movimientos no explicados)", "Revisión mensual"],
    ["Reporte de Operación Sospechosa a la UAF, con deber de reserva", "Dentro de 48 horas desde la detección"],
    ["Actualización del perfil e idoneidad de los instrumentos", "Anual o ante un cambio material"],
    ["Conservación de registros", "Mínimo 5 años"]], w=[11.5, 4.5])
H("2.3 Perfil del inversionista", 2)
P("María Ignacia (40 años, abogada en consumo masivo) y Tomás (46, ingeniero en software) tienen dos hijos (Vicente, 4; Emilia, 2), ingresos estables y educación financiera media, sin experiencia en derivados ni criptoactivos. El perfil distingue dos dimensiones:")
TB(["Dimensión", "Evidencia", "Conclusión"], [
    ["Capacidad de riesgo (objetiva)", f"Capital USD 150.000 + valor presente de los aportes (~USD 150.000 a 2,5% real); sin necesidades de liquidez hasta el año 14; horizonte hasta 50 años", "Alta en el largo plazo; decreciente frente a Educación (años 14-20)"],
    ["Disposición al riesgo (conductual)", "Toleran hoy 85% en activos de riesgo (cartera AGF) y piden activamente commodities y alternativos", "Moderada-agresiva; renta variable de 60-65%"],
    ["Capital humano", "El ingreso de Tomás depende del sector software (se comporta como una acción tecnológica); el de María Ignacia, de consumo masivo (como un bono)", "Limitar tecnología: ~14% en Nexum vs ~26% en la AGF"],
    ["Aversión al riesgo (A)", f"A del inversionista de mercado (S&P 500, 2013-2026) = {n_(av[0],1)}; A implícito en la cartera recomendada = {n_(av[1],1)}; δ de Black-Litterman = {n_(av[2],1)}", "El cliente acepta más riesgo que el inversionista promedio, coherente con su horizonte"]], w=[3.4, 7.6, 5])
P("El cuestionario de tolerancia al riesgo (Grable y Lytton) se aplicará directamente a ambos clientes en la reunión de inicio; si su resultado difiere de este perfil, se revisará el IPS. No se usan respuestas simuladas.", it=True, sz=9)
H("2.4 Objetivos, prioridad y horizontes", 2)
pd_ = T["Plan_desembolsos"]
TB(["Prioridad", "Objetivo (moneda del cliente)", "Años", "UF", "USD reales", "Flexibilidad"], [
    ["1", "Educación: CLP 65 millones por hijo, en 5 pagos anuales", "14-18 y 16-20", n_(pd_[pd_.Concepto == 'Educación']['UF'].sum(), 0), n_(pd_[pd_.Concepto == 'Educación']['USD reales'].sum(), 0), "Rígida, no diferible"],
    ["2", "Villarrica: desembolso UF 10.500 (UF 15.000 adicionales vienen de la venta de la casa, fuera de la cartera)", "25", "10.500", n_(VILLARRICA_UF * UF_CLP / USD_CLP, 0), "Postergable o reducible"],
    ["3", "Herencia: USD 250.000 por hijo, en dinero de hoy", "50", n_(HERENCIA_USD * USD_CLP / UF_CLP, 0), "500.000", "Residual: absorbe la variabilidad"]], w=[1.5, 6.4, 1.9, 1.6, 1.9, 2.7])
P("La herencia tiene el mayor monto pero la menor prioridad: no tiene fecha rígida y es la variable de ajuste natural. Villarrica tiene fecha, pero el propio enunciado admite postergación, reducción de superficie o una localización alternativa. Educación no admite sustitución. Horizontes: corto plazo (menos de 3 años antes de cada pago de Educación), mediano plazo (3 a 15 años) y largo plazo (Villarrica y herencia). Entre los años 16 y 18 se pagan las dos carreras a la vez: es la mayor carga de liquidez del plan.")
H("2.5 Retorno requerido y factibilidad", 2)
FIGURA("f5_tir.png", "Figura 1. TIR real requerida por escenario. Fuente: codigo/objetivos.py; hoja 02_Objetivos_TIR (fórmula IRR).")
P(f"A la tasa real libre de riesgo, los recursos cubren {n_(fac['Cobertura (recursos / objetivos)'],2)} veces los objetivos: el plan es factible solo si la cartera captura prima por riesgo. Valorizados a la TIR, Villarrica representa {p_(fac['Peso VP Villarrica'],0)} de la exigencia, Educación {p_(fac['Peso VP Educación'],0)} y la herencia {p_(fac['Peso VP Herencia'],0)}. No se usa la venta de la casa de Santiago más allá de las UF 15.000 que el enunciado asigna a Villarrica.")
TB(["Año", "Concepto", "UF", "USD reales"], [[int(r["Año"]), r["Concepto"][:80], n_(r["UF"], 1), n_(r["USD reales"], 0)] for _, r in pd_.iterrows()], w=[1.3, 10, 2.2, 2.5], nota="Plan de desembolsos. Tipo de cambio de corte: UF = CLP 40.846; USD = CLP 911,77 (BCCh, 11-ago-2026).")
H("2.6 Restricciones", 2)
B([("Liquidez: ", "sin retiros hasta el año 14; reserva operativa de 4% del capital (2% caja + 2% reserva cambiaria); fondo de emergencia fuera del mandato."),
   ("Legales y tributarias: ", "ETF y acciones listadas en EE.UU.; retención de 15% sobre dividendos por el convenio Chile-EE.UU.; tributación en Chile al liquidar."),
   ("Éticas e idoneidad (CFA, Estándar III.C): ", "sin derivados complejos, criptoactivos, apalancamiento ni ventas cortas, por el nivel de conocimiento declarado. Única excepción: forwards de venta de USD contra CLP con un banco regulado, solo como cobertura cambiaria (monto menor al valor de la cartera y plazo de hasta un año), explicados a los clientes y aceptados por ellos (sección 3.4)."),
   ("Plataforma: ", "instrumentos disponibles en StockTrak; al menos 150 operaciones en 12 semanas y 5 por semana en promedio.")])
H("2.7 Asignación estratégica y riesgo-retorno esperado", 2)
FIGURA("f3_asignacion.png", "Figura 2. Pesos Black-Litterman (aprobados) frente al prior de paridad de riesgo y a Markowitz histórico. Fuente: hojas 05 y 06 del modelo.")
P("Marco: Black-Litterman parte de un prior de equilibrio de paridad de riesgo (peso inverso a la volatilidad), deriva retornos implícitos π = δΣw y los combina con dos vistas explícitas: el S&P 500 rinde 6% (prima por riesgo de largo plazo) y Low-Volatility supera a commodities en 2 puntos. La optimización restringe el núcleo pasivo entre 60% y 70%. Markowitz con medias históricas se reporta solo como referencia: concentra en lo que más rindió en el pasado (ver walk-forward, sección 4.4).")
P(f"Los pesos aprobados en septiembre siguen vigentes: recalibrados con los datos corregidos de esta versión, difieren en menos de {n_(abs(asg['Diferencia (pp)']).max(),1)} puntos, dentro de la banda de rebalanceo de ±2 puntos. Cambiarlos solo generaría costos.")
m16 = lambda s, k: mt('2016-2026', s, k)
TB(["Métrica (2016-2026, USD)", "Nexum", "Benchmark", "AGF 85/15", "S&P 500"],
   [[k] + [(p_(m16(s, k)) if k not in ("Sharpe", "Sortino", "Beta", "Information ratio") else n_(m16(s, k))) for s in ["Cartera Nexum", "Benchmark de política", "Cartera actual AGF 85/15", "S&P 500 (SPY)"]]
    for k in ["CAGR", "Volatilidad", "Sharpe", "Sortino", "Beta", "Máx. caída", "VaR 95% mensual", "CVaR 95% mensual", "Tracking error", "Information ratio"]], w=[5, 2.7, 2.7, 2.7, 2.7])
P(f"Retorno esperado vs requerido: el retorno histórico real 2013-2026 fue {p_(g('Nexum','Hist','USD','Retorno real anual'))}, muy sobre el requerido. Con supuestos prospectivos (tasa real ~2,5% más primas moderadas; sección 4.3) el retorno real esperado es {p_(g('Nexum','Prosp','USD','Retorno real anual'))}, igual al requerido de {p_(fac['TIR requerida'],2)}. Nivel de riesgo aceptable: volatilidad anual de 10-12%, máxima caída tolerada de 25% y probabilidad de Educación de al menos 90%.")
rcd = T["Contribucion_riesgo"]
FIGURA("f8_riesgo.png", "Figura 3. Peso de cada activo frente a su contribución al riesgo total (pesos aprobados, covarianza 2013-2026). Fuente: hoja 06 del modelo.")
P(f"Contribución al riesgo: el S&P 500 pesa {p_(rcd.iloc[0]['Peso'])} pero aporta {p_(rcd.iloc[0]['Contribución al riesgo (%)'])} del riesgo; Momentum pesa {p_(rcd.iloc[4]['Peso'])} y aporta {p_(rcd.iloc[4]['Contribución al riesgo (%)'])}. Los bonos del Tesoro diversifican: con {p_(rcd.iloc[1]['Peso'])} del capital aportan solo {p_(rcd.iloc[1]['Contribución al riesgo (%)'])}. El presupuesto de riesgo está dominado por la renta variable, coherente con un perfil moderado-agresivo que necesita prima por riesgo para cumplir sus objetivos.")
FIGURA("f1_crecimiento.png", "Figura 4. Crecimiento de USD 100 (2016-2026). Fuente: resultados/retornos_cartera_benchmark.csv.")
FIGURA("f2_caidas.png", "Figura 5. Caídas desde el máximo: Nexum frente a la cartera actual de la AGF.")
H("2.8 Selección, seguimiento y rebalanceo", 2)
TB(["Elemento", "Regla"], [
    ["Selección", "Núcleo: ETF líquidos de bajo costo. Satélite: acciones del S&P 500 (precio ≥ USD 5, liquidez ≥ USD 5 millones/día) y 5 ETF de commodities"],
    ["Señales", "Mensuales, con el cierre del último día hábil (codigo/senales.py); ejecución escalonada durante la semana siguiente"],
    ["Bandas", "Núcleo ±5 puntos por activo; satélite ±2 puntos por sleeve; dentro de cada sleeve, peso igual"],
    ["Revisión semanal", "Ranking de Momentum con banda de permanencia: una acción se mantiene mientras esté en el top 25"],
    ["Costos", "No se ejecutan ajustes menores a USD 500 (comisión de USD 10 = 2% del monto)"],
    ["Disciplina de venta", "Núcleo sin stop-loss (se controla con bandas). Satélite: salida por señal; stop de emergencia de −15%; en posiciones con ganancia, stop móvil sobre el costo"],
    ["Eventos", "No se ejecuta en la primera media hora ni durante la publicación de datos de la Fed, inflación o empleo"],
    ["Cobertura cambiaria", "Forward de venta de USD a un año por ~70% de la cartera (sección 3.4); al vencimiento se evalúa renovarlo con la razón de cobertura vigente"]], w=[3.6, 12.4])
bd = AD["Bandas_rebalanceo"].set_index("Regla")
P(f"Las bandas no son restrictivas. En el backtest 2013-2026, las bandas vigentes (±5 / ±2) se activan {n_(bd.loc['Bandas ±5 / ±2 pp (vigente)','Rebalanceos por año'],1)} veces al año (~{n_(bd.loc['Bandas ±5 / ±2 pp (vigente)','Órdenes por año'],0)} órdenes) y mantienen la cartera a {p_(bd.loc['Bandas ±5 / ±2 pp (vigente)','Desvío vs. pesos fijos (TE)'])} de tracking error de los pesos aprobados. Bandas de ±3 / ±1 duplicarían los rebalanceos ({n_(bd.loc['Bandas ±3 / ±1 pp','Rebalanceos por año'],1)} al año) sin mejorar el resultado, y el rebalanceo mensual exigiría ~{n_(bd.loc['Mensual por calendario','Órdenes por año'],0)} órdenes al año. No rebalancear nunca deja la cartera con {p_(bd.loc['Sin rebalanceo','Desvío vs. pesos fijos (TE)'])} de desvío y más volatilidad ({p_(bd.loc['Sin rebalanceo','Volatilidad'])} vs {p_(bd.loc['Bandas ±5 / ±2 pp (vigente)','Volatilidad'])}). Las operaciones que exige StockTrak provienen de la rotación dentro de los sleeves activos, no de las bandas.")
H("2.9 Política de revisión y control", 2)
B(["Revisión anual del IPS y del Montecarlo con datos actualizados.",
   "Revisión extraordinaria si: la probabilidad de Educación cae bajo 90%; la cartera cae más de 15% desde su máximo; el tracking error supera 4%; Tomás pierde su empleo; cambia algún objetivo.",
   "Informe mensual al cliente (desempeño frente al benchmark, operaciones y riesgos) y reunión trimestral, donde los clientes participan en las decisiones tácticas."])

# ================= 3. ESTRATEGIA =================
d.add_page_break(); H("3. Estrategia de inversión")
H("3.1 Arquitectura núcleo-satélite", 2)
P("El núcleo pasivo (69%) captura la prima de mercado y de plazo a bajo costo y es la base de financiamiento de largo plazo. El satélite (31%) busca primas de factores documentadas, con un presupuesto de riesgo activo acotado. Las tres estrategias se eligieron porque se complementan: Momentum aporta retorno en mercados con tendencia, Low-Volatility reduce la beta de la cartera y Momentum en commodities diversifica frente a acciones y bonos.")
H("3.2 Estrategias activas: evidencia y resultados", 2)
TB(["Estrategia", "Implementación", "Evidencia académica", "Riesgo/retorno teórico"], [
    ["Momentum en acciones", "Top 10 del S&P 500 por 50% retorno 6m + 50% retorno 12m; filtros de tendencia y liquidez; máx. 25% por sector; mensual",
     "Jegadeesh y Titman (1993); Carhart (1997); Asness, Moskowitz y Pedersen (2013)", "Ganadores menos perdedores ~1% mensual (J&T, 1965-1989); caídas abruptas en rebotes del mercado (Daniel y Moskowitz, 2016)"],
    ["Low-Volatility", "Top 10 del S&P 500 por menor volatilidad 12m; peso igual; máx. 25% por sector; solo compras",
     "Haugen y Heins (1975); Ang et al. (2006); Blitz y van Vliet (2007); Baker, Bradley y Wurgler (2011)", "Retorno similar al mercado con ~30% menos volatilidad; beta 0,5-0,7"],
    ["Momentum en commodities", "GLD, USO, DBA, SLV, CPER: compra los que superan filtros de tendencia 3/6/12 meses y media de 200 días, con vol. < 50%",
     "Erb y Harvey (2006); Miffre y Rallis (2007); Moskowitz, Ooi y Pedersen (2012)", "Prima del orden de 9% anual en futuros (Miffre y Rallis); baja correlación con acciones y bonos"]], w=[2.8, 5, 4.2, 4.2], sz=8)
TB(["Estrategia (2016-2026)", "Benchmark", "Retorno anual", "Volatilidad", "Sharpe", "Beta", "Máx. caída", "TE", "IR"],
   [[NOM, BEN, p_(esv(NOM, "CAGR")), p_(esv(NOM, "Volatilidad")), n_(esv(NOM, "Sharpe")), n_(esv(NOM, "Beta")), p_(esv(NOM, "Máx. caída")), p_(esv(NOM, "Tracking error")), n_(esv(NOM, "Information ratio"))]
    for NOM, BEN in [("Momentum en acciones", "QMOM"), ("Low-Volatility", "SPLV"), ("Momentum en commodities", "Mezcla 5 ETF")]], w=[3.6, 2.2, 1.7, 1.7, 1.3, 1.2, 1.7, 1.3, 1.3], sz=8)
P("Fundamento de los filtros: 6 y 12 meses son las ventanas de formación estándar (Jegadeesh y Titman, 1993); la media de 200 días es un filtro de tendencia clásico (Faber, 2007); el filtro de Sharpe descarta alzas con volatilidad excesiva, en la línea del control de volatilidad de Barroso y Santa-Clara (2015); el límite sectorial controla la concentración en tecnología, que además es el riesgo del capital humano de Tomás.")
P("Lo que se implementa es Low-Volatility y no Betting Against Beta: la estrategia de Frazzini y Pedersen (2014) apalanca las acciones de beta baja y vende en corto las de beta alta. Nexum no usa apalancamiento ni ventas cortas, así que su retorno proviene de la anomalía de baja volatilidad y conserva una beta de ~0,55.")
P(f"Discusión crítica. (i) Las primas de factores se reducen fuera de muestra y después de su publicación (McLean y Pontiff, 2016), por eso los supuestos prospectivos usan primas menores a las históricas. (ii) Momentum sufre caídas abruptas cuando el mercado rebota. (iii) Low-Volatility se concentra en utilities y REITs, sensibles a tasas; en septiembre de 2026 se observó en vivo, con la tasa a 10 años en 5,3%. (iv) Momentum en commodities es sensible a sus umbrales y su universo se amplió mirando el backtest (sección 4.4): con el universo original de 3 ETF su Sharpe cae de {n_(rbv('Commodities','BASE'))} a {n_(rbv('Commodities','Universo original'))}. Por eso es el sleeve con menor peso.")
H("3.3 Alternativas evaluadas y descartadas", 2)
B(["Rotación sectorial con ETF: misma familia que Momentum (correlación ~0,67) y no mejora el Sharpe de la cartera; se pierde el rol defensivo de Low-Vol.",
   "Reversión de corto plazo semanal: ~19 operaciones por semana; los costos (~10% anual a 0,1% por lado y peor con la comisión fija de StockTrak) eliminan su prima.",
   "Momentum de 4 semanas y estrategias semanales: Sharpe neto de costos de 0,2 a 0,5, inferior a las estrategias mensuales.",
   "Betting Against Beta: requiere apalancamiento y ventas cortas, excluidos por idoneidad."])
aa = AD["Activos_adicionales"].set_index("Variante"); a_agg = aa.loc["Duración intermedia: 50% de la renta fija en AGG"]; a_efa = aa.loc["Internacional: 5 pp del S&P 500 a EFA"]; a_0 = aa.loc["Vigente"]
P("Activos adicionales evaluados (octubre de 2026). Agregar un activo cambia la asignación estratégica, por lo que exige recalibrar Black-Litterman y modificar este IPS; no es una decisión de rebalanceo. Se evaluaron los dos candidatos con datos suficientes:")
TB(["Variante", "Retorno anual", "Volatilidad", "Sharpe", "Máx. caída", "TE", "P(3) histórico", "P(3) prospectivo"],
   [[k, p_(r["Retorno anual"]), p_(r["Volatilidad"]), n_(r["Sharpe"]), p_(r["Máx. caída"]), p_(r["TE vs. benchmark de política"]), p_(r["P(3 objetivos) histórico"]), p_(r["P(3 objetivos) prospectivo"])] for k, r in aa.iterrows()],
   w=[5.2, 1.6, 1.6, 1.2, 1.6, 1.2, 1.8, 1.8], sz=7.5,
   nota="Backtest 2013-2026 en USD. Prospectivo: supuesto propio de 2,4% real para AGG (menor duración que TLH, 2,6%) y 5,5% para EFA. Fuente: codigo/analisis_adicional.py.")
B([("Bonos de duración intermedia (AGG, proxy de VCIT o SCHP): ", f"bajan la volatilidad ({p_(a_0['Volatilidad'])} → {p_(a_agg['Volatilidad'])}) y la caída máxima, pero con supuestos prudentes la probabilidad conjunta cae de {p_(a_0['P(3 objetivos) prospectivo'])} a {p_(a_agg['P(3 objetivos) prospectivo'])}, porque el plan necesita la prima por plazo. TLH además diversifica mejor que AGG frente al S&P 500. Se mantiene la renta fija larga y se reevalúa en la revisión anual."),
   ("Acciones internacionales (EFA): ", f"correlación de 0,82 con el S&P 500; en el backtest empeoran el resultado ({p_(a_efa['P(3 objetivos) histórico'])} vs {p_(a_0['P(3 objetivos) histórico'])}) y hacia adelante suman menos de un punto ({p_(a_efa['P(3 objetivos) prospectivo'])}). No justifican un cambio de política.")])
H("3.4 Moneda funcional: USD, con simulaciones en UF y cobertura con forward", 2)
fx = T["Riesgo_cambiario"].set_index("Indicador")["Valor"]
P("La moneda funcional es el USD porque todo el universo de inversión cotiza en dólares. Las necesidades del cliente (UF/CLP) se evalúan explícitamente: el Montecarlo se presenta también en UF y, desde el 28-sep-2026, parte del riesgo cambiario de corto plazo se cubre con un forward (ver más abajo).")
B([("Cobertura natural: ", f"el peso se deprecia cuando caen los mercados globales (correlación S&P 500 vs. USD/CLP de {n_(fx.iloc[1])}). En el 10% de los peores meses del S&P 500 el dólar subió {p_(fx.iloc[2])} en promedio: la cartera perdió {p_(fx.iloc[3])} en USD pero solo {p_(fx.iloc[4])} medida en pesos."),
   ("Diversificación del riesgo país: ", "el capital humano y la vivienda de la familia ya están expuestos a Chile."),
   ("Costo: ", f"la volatilidad del USD/CLP es {p_(fx.iloc[0])} anual; medida en pesos, la volatilidad de la cartera sube de {p_(fx.iloc[5])} a {p_(fx.iloc[6])}, y la probabilidad conjunta histórica baja de {p_(g('Nexum','Hist','USD','P(3 objetivos)'))} a {p_(g('Nexum','Hist','UF','P(3 objetivos)'))}. Se monitorea en cada revisión.")])
H("Cobertura cambiaria con forward USD/CLP", 3)
fc = AD["Forward_condiciones"].set_index("Concepto")["Valor"]; fs = AD["Forward_simulacion"]; fl = AD["Forward_liquidacion"].set_index("Indicador")["Valor"]
fr = AD["Forward_razon_cobertura"]; h_opt = fr.loc[fr["Volatilidad 12m en CLP"].idxmin(), "Razón de cobertura"]
fv = lambda m, cart, k: fs[fs["Medido en"].str.startswith(m) & (fs.Cartera == cart)][k].iloc[0]
P(f"El 28 de septiembre de 2026 Nexum contrató un forward con {fc['Contraparte']}: vende USD {n_(fc['Monto (USD)'],0)} a CLP {n_(fc['Precio forward (CLP por USD)'])} por dólar, con vencimiento el 30 de septiembre de 2027. El precio es el spot de CLP {n_(fc['Tipo de cambio spot (CLP por USD)'])} menos {n_(-fc['Puntos forward'])} puntos forward. Los puntos negativos reflejan que la tasa en pesos es menor que la tasa en dólares (paridad cubierta de tasas): cubrirse cuesta {p_(-fc['Puntos como % del spot (≈ tasa CLP − tasa USD)'],2)} del monto, unos USD {n_(-fc['Costo de la cobertura a spot constante (USD)'],0)} si el dólar no se mueve. El contrato no se opera en StockTrak; se registra y valoriza aparte.")
TB(["Dólar al vencimiento (CLP)", "Compensación (MM CLP)", "Compensación (USD)", "Para Nexum"],
   [[n_(r["Dólar al vencimiento (CLP)"]), n_(r["Compensación (MM CLP)"]), n_(r["Compensación (USD)"], 0), r["Lectura"]] for _, r in AD["Forward_escenarios"].iterrows()], w=[4, 4, 4, 4],
   nota="Compensación = USD 104.000 × (precio forward − dólar al vencimiento). Si el dólar sube, Nexum paga la diferencia, pero la cartera en USD vale más en pesos; si baja, Nexum recibe la diferencia y compensa la pérdida de valor en pesos.")
P(f"Por qué ese monto. USD 104.000 cubren {p_(fc['Cobertura sobre el mandato (USD 150.000)'],0)} del mandato ({p_(fc['Cobertura sobre el valor al 28-sep'],0)} del valor de la cartera ese día). Como el peso se deprecia cuando caen los mercados (cobertura natural, correlación {n_(fl['Correlación cartera Nexum vs. Δ USD/CLP (mensual)'])}), cubrir el 100% no minimiza el riesgo en pesos: en la simulación, la volatilidad en pesos es mínima con una cobertura de ~{p_(h_opt,0)}, muy cerca del {p_(fc['Cobertura sobre el valor al 28-sep'],0)} contratado.")
TB(["Medido en", "Cartera", "Retorno medio 12 meses", "Volatilidad", "Peor 5%", "P(pérdida > 10%)"],
   [[r["Medido en"], r["Cartera"], p_(r["Retorno medio 12m"]), p_(r["Volatilidad"]), p_(r["Peor 5%"]), p_(r["P(pérdida > 10%)"])] for _, r in fs.iterrows()], w=[4.2, 2.8, 2.6, 2.2, 2, 2.4],
   nota="20.000 escenarios de 12 meses por bootstrap de los retornos mensuales conjuntos de la cartera y del USD/CLP (2013-2026), con el dólar sin tendencia. Fuente: codigo/analisis_adicional.py.")
P(f"Lectura. Medido en pesos, la moneda de las metas, el forward baja la volatilidad de {p_(fv('CLP','Sin cobertura','Volatilidad'))} a {p_(fv('CLP','Con el forward','Volatilidad'))} y el peor 5% de {p_(fv('CLP','Sin cobertura','Peor 5%'))} a {p_(fv('CLP','Con el forward','Peor 5%'))}. Medido en dólares, la aumenta ({p_(fv('USD','Sin cobertura','Volatilidad'))} → {p_(fv('USD','Con el forward','Volatilidad'))}): en los peores años de la cartera el peso se deprecia y el forward se paga (en promedio USD {n_(-fl['Compensación media en el 10% de peores años de la cartera en USD'],0)} en el 10% de peores años). Es el costo de medir el riesgo en la moneda de las metas, que es la que importa para la familia.")
P(f"Liquidez. En {p_(fl['Probabilidad de pagar más que la reserva cambiaria (USD 3.000)'],0)} de los escenarios la compensación supera la reserva cambiaria de 2% (USD 3.000, que alcanza hasta un dólar de CLP {n_(fc['Tipo de cambio que agota la reserva cambiaria de 2% (USD 3.000)'],0)}); en el 5% más adverso Nexum paga ~USD {n_(fl['Pago en el 5% de escenarios más adversos (USD)'],0)}. Ese pago se financia con SGOV y venta de activos en USD, que en ese mismo escenario valen más en pesos. El valor de mercado del forward se informa mensualmente y la renovación se decide al vencimiento.")
H("3.5 Benchmark de política", 2)
TB(["Sleeve", "Peso", "Benchmark (índice invertible del mismo universo)"], [
    ["S&P 500", "37,9%", "S&P 500 (SPY)"], ["Tesoro 10-20 años", "16,9%", "ICE U.S. Treasury 10-20 Year Index (TLH)"], ["Corporativos largo plazo", "14,6%", "Bloomberg U.S. Long Corporate Index (VCLT)"],
    ["Momentum en acciones", "7,1%", "Alpha Architect U.S. Quantitative Momentum (QMOM)"], ["Low-Volatility", "17,5%", "S&P 500 Low Volatility Index (SPLV)"],
    ["Momentum en commodities", "6,1%", "Mezcla igual ponderada GLD/USO/DBA/SLV/CPER"]], w=[4.2, 1.6, 10.2],
   nota="Benchmark compuesto ponderado por la asignación estratégica y expresado en USD. Reemplaza la tasa de política de la Fed y el MSCI ACWI de la versión anterior, que no eran invertibles ni representaban el universo. Limitación: QMOM existe desde dic-2015, por lo que las métricas relativas usan 2016-2026.")
H("Benchmark por clase de activo", 3)
bc = AD["Benchmark_clases"]; bc16 = bc[bc["Período"] == "2016-2026"].set_index("Clase"); bk = AD["Benchmark_compuesto"]
bkv = lambda per, s, k: bk[(bk["Período"] == per) & bk.Serie.str.startswith(s)][k].iloc[0]
P("El benchmark por sleeve mide si cada estrategia cumple su regla. El benchmark por clase de activo responde otra pregunta: si las decisiones dentro de cada clase (factores en renta variable, duración en renta fija, señal en commodities) agregan valor frente al índice amplio de esa clase. Cada clase se compara con un índice invertible del mismo universo:")
TB(["Clase (peso)", "Benchmark", "Retorno Nexum", "Retorno benchmark", "Vol. Nexum / benchmark", "Máx. caída Nexum / benchmark", "TE", "Aporte al retorno activo"],
   [[f"{k} ({p_(r['Peso'])})", r["Benchmark"], p_(r["Retorno Nexum"]), p_(r["Retorno benchmark"]), f"{p_(r['Vol. Nexum'])} / {p_(r['Vol. benchmark'])}",
     f"{p_(r['Máx. caída Nexum'])} / {p_(r['Máx. caída benchmark'])}", p_(r["Tracking error"]), f"{n_(r['Aporte a la cartera (pp)'] * 100)} pp"] for k, r in bc16.iterrows()]
   + [["Liquidez (reserva 4%)", "T-Bills 0-3 meses (BIL/SGOV)", "—", "—", "—", "—", "—", "fuera de la asignación"]],
   w=[3, 3.3, 1.5, 1.6, 2, 2.2, 1.1, 1.6], sz=7.5,
   nota="2016-2026, USD. Renta fija: 50% TLH + 50% VCLT como proxy invertible del Bloomberg U.S. Long Government/Credit (BLV no está en la base de datos). Commodities: el Bloomberg Commodity Index sería el índice amplio, pero no está en la base; se usa la mezcla igual ponderada de los 5 ETF. Fuente: codigo/analisis_adicional.py.")
rv = bc16.loc["Renta variable EE.UU."]
P(f"Lectura. El benchmark por clase rindió {p_(bkv('2016-2026','Benchmark por clase','CAGR'))} anual frente a {p_(bkv('2016-2026','Cartera Nexum','CAGR'))} de Nexum (tracking error {p_(bkv('2016-2026','Cartera Nexum','Tracking error'))}, dentro del objetivo de 3%). Casi toda la diferencia viene de la renta variable: Low-Volatility y Momentum rindieron {n_(-rv['Retorno activo anual']*100)} puntos menos al año que el S&P 500 en una década excepcional para el índice, pero con menos volatilidad ({p_(rv['Vol. Nexum'])} vs {p_(rv['Vol. benchmark'])}), una caída máxima menor ({p_(rv['Máx. caída Nexum'])} vs {p_(rv['Máx. caída benchmark'])}) y el mismo Sharpe ({n_(rv['Sharpe Nexum'])} vs {n_(rv['Sharpe benchmark'])}). Es decir, el satélite de renta variable cumplió su función de bajar el riesgo, no de superar al índice. La renta fija es pasiva y replica su benchmark (TE {p_(bc16.loc['Renta fija larga EE.UU.','Tracking error'])}). En 2013-2026 el resultado es similar ({p_(bkv('2013-2026','Cartera Nexum','CAGR'))} vs {p_(bkv('2013-2026','Benchmark por clase','CAGR'))}), con un aporte positivo de commodities.")
du = AD["Duracion_renta_fija"]
P(f"Decisión de duración. Frente a los bonos amplios de EE.UU. (AGG, duración ~6), la renta fija larga de Nexum rindió casi lo mismo en 2013-2026 ({p_(du.iloc[0]['Retorno anual'])} vs {p_(du.iloc[1]['Retorno anual'])}) con el doble de volatilidad, protegió más en la crisis de 2020 ({p_(du.iloc[0]['Feb-mar 2020 (S&P 500 −19%)'])} vs {p_(du.iloc[1]['Feb-mar 2020 (S&P 500 −19%)'])}) y cayó más en el alza de tasas de 2022 ({p_(du.iloc[0]['2022 (alza de tasas)'])} vs {p_(du.iloc[1]['2022 (alza de tasas)'])}). La duración larga es una decisión estratégica coherente con metas a 14-50 años, y por eso el benchmark de la clase es el Bloomberg U.S. Long Government/Credit Index (duración ~14, igual a la nuestra) y no el Bloomberg U.S. Aggregate (AGG).")
H("3.6 Métricas de desempeño", 2)
TB(["Métrica", "Para qué se usa", "Limitación"], [
    ["Sharpe", "Retorno por unidad de riesgo total", "Supone normalidad; penaliza la volatilidad al alza"],
    ["Sortino", "Penaliza solo la volatilidad a la baja", "Inestable con pocas observaciones"],
    ["Treynor y alfa de Jensen", "Retorno por unidad de riesgo sistemático y valor agregado ajustado por beta", "Dependen del modelo de mercado y del beta estimado"],
    ["Tracking error e information ratio", "Riesgo activo y su eficiencia frente al benchmark", "Requieren un benchmark bien construido"],
    ["Máxima caída y Calmar", "Tolerancia conductual a pérdidas", "Dependen de la ventana"],
    ["VaR y CVaR 95% mensual", "Pérdida en un mes malo y en la cola", "El VaR no informa el tamaño de la cola; por eso se agrega CVaR"],
    ["Probabilidad de éxito por objetivo", "Métrica central de un IPS por objetivos", "Depende de los supuestos del Montecarlo"]], w=[4, 6.2, 5.8])
H("3.7 Tracking error objetivo", 2)
P(f"El límite se deriva del presupuesto de riesgo activo (Grinold y Kahn, 2000): con un alfa objetivo de 1,5% anual y un information ratio objetivo de 0,5, el TE objetivo es 1,5% / 0,5 = 3,0%; el máximo es 4% (alfa de 2% con el mismo IR). El TE ex-ante con los pesos aprobados es {p_(te.iloc[0])} (2016-2026) y {p_(te.iloc[1])} en los últimos 36 meses, dentro del objetivo; el information ratio realizado es {n_(mt('2016-2026','Cartera Nexum','Information ratio'))}.")

# ================= 4. BACKTEST Y MONTECARLO =================
d.add_page_break(); H("4. Backtesting y simulación de Montecarlo")
H("4.1 Datos, período y supuestos", 2)
B(["Acciones del S&P 500 con membresía histórica point-in-time (2009-2026): sin sesgo de supervivencia en los miembros del índice.",
   "ETF del núcleo, de commodities y benchmarks: Yahoo Finance, precios ajustados por dividendos.",
   "Ventana de evaluación: ene-2013 a ago-2026 (164 meses); métricas relativas, 2016-2026 (128 meses).",
   "Señal con información disponible al cierre del mes t; retorno desde t+1 (sin anticipación). Costo de 0,1% sobre la rotación.",
   "Montecarlo: 20.000 escenarios de 50 años por bootstrap mensual; inflación de EE.UU. de 2%; capital invertido de USD 144.000 (neto de la reserva de 4%)."])
H("4.2 Montecarlo: probabilidad de cumplir los objetivos", 2)
FIGURA("f4_montecarlo.png", "Figura 6. Probabilidad de cumplir cada objetivo. Fuente: codigo/montecarlo.py; hoja 08_Montecarlo.")
TB(["Cartera", "Escenario", "Moneda", "Retorno real", "P(Educación)", "P(Villarrica)", "P(Herencia)", "P(3 objetivos)"],
   [[r.Cartera, r.Escenario, r.Moneda, p_(r["Retorno real anual"]), p_(r["P(Educación)"]), p_(r["P(Villarrica)"]), p_(r["P(Herencia)"]), p_(r["P(3 objetivos)"])] for _, r in mc.iterrows()],
   w=[2, 3.2, 1.4, 1.7, 1.9, 1.9, 1.9, 2], sz=8,
   nota="Escenario prospectivo: misma volatilidad y correlaciones históricas, con medias ajustadas a supuestos de mercado (retornos reales: S&P 500 5,0%, Low-Vol 4,5%, Momentum 5,5%, TLH 2,6%, VCLT 3,2%, commodities 2,0%). UF: tipo de cambio real sin tendencia, con la volatilidad y la correlación observadas.")
P("Interpretación: Educación se cumple en prácticamente todos los escenarios, por lo que el piso de diseño (90-95%) se satisface con holgura. La incertidumbre se concentra en Villarrica y la herencia, que el IPS define como flexibles. Con retornos históricos el plan es holgado; con supuestos prudentes la probabilidad conjunta es menor a 50%, coherente con un retorno esperado que apenas iguala al requerido. Esta es la conclusión que se presenta a los clientes, junto con las palancas de ajuste:")
TB(["Palanca (escenario prospectivo, USD)", "P(Educación)", "P(Villarrica)", "P(Herencia)", "P(3 objetivos)"], [[k] + [p_(v) for v in r.values] for k, r in pal.iterrows()], w=[6.4, 2.4, 2.4, 2.4, 2.4])
FIGURA("f7_abanico.png", "Figura 7. Abanico del patrimonio real (percentiles 10-90). Escalas distintas en cada panel. La caída del año 25 es la compra de Villarrica.")
abp = T["Abanico_prospectivo"].set_index("Año")
P(f"Distribución del patrimonio (prospectivo, USD de hoy): al iniciar Educación (año 14) la mediana es {u_(abp.loc[14,'P50'])} y el 10% peor {u_(abp.loc[14,'P10'])}, muy por sobre los ~USD 143.000 que cuesta Educación completa; antes de Villarrica (año 25) la mediana es {u_(abp.loc[25,'P50'])} frente a un desembolso de ~USD 470.000; al año 50 la mediana es {u_(abp.loc[50,'P50'])}, bajo la meta de herencia de USD 500.000. Es la misma conclusión de la TIR: Educación está holgada, Villarrica es ajustada y la herencia es la variable de ajuste.")
H("Capital humano: desempleo de Tomás", 3)
de = T["Desempleo"]; dv = lambda e, m, k: de[(de["Escenario de empleo"].str.startswith(e)) & (de.Mercado == m)][k].iloc[0]
TB(["Escenario de empleo", "Mercado", "P(Educación)", "P(Villarrica)", "P(Herencia)", "P(3 objetivos)"],
   [[r["Escenario de empleo"], r["Mercado"], p_(r["P(Educación)"]), p_(r["P(Villarrica)"]), p_(r["P(Herencia)"]), p_(r["P(3 objetivos)"])] for _, r in de.iterrows()],
   w=[6.6, 2, 1.8, 1.9, 1.8, 1.9], sz=7.5,
   nota="El empleo de Tomás (software) se comporta como una acción tecnológica: la probabilidad de perderlo sube cuando la cartera cae. Mientras está desempleado no aporta; se reemplea con 50% anual (~2 años en promedio). El escenario de estrés supone pérdida permanente.")
P(f"Lectura: Educación resiste incluso la pérdida permanente del empleo ({p_(dv('Estrés','Prospectivo','P(Educación)'))} en el escenario prospectivo). El riesgo de capital humano recae sobre Villarrica y la herencia: con desempleo correlacionado con el mercado, la probabilidad conjunta histórica baja de {p_(dv('Sin','Histórico','P(3 objetivos)'))} a {p_(dv('10%','Histórico','P(3 objetivos)'))}. Mitigantes: fondo de emergencia fuera del mandato, seguro de vida e invalidez, y el límite a tecnología en la cartera para no duplicar la exposición del ingreso de Tomás.")
H("4.3 Validación del modelo", 2)
P("Correcciones respecto de la versión anterior del modelo. La auditoría encontró tres problemas que afectaban los resultados; esta versión los corrige y mide su efecto:")
TB(["Versión", "Meses", "Momentum", "Low-Vol", "Commod.", "Cartera CAGR", "Sharpe", "BL SPY", "BL LV"],
   [[r["Versión"][:52], int(r["Meses"]), p_(r["CAGR Momentum"]), p_(r["CAGR Low-Vol"]), p_(r["CAGR Commodities"]), p_(r["Cartera (pesos aprobados) CAGR"]), n_(r["Cartera Sharpe"]), p_(r["BL SPY"]), p_(r["BL LOW_VOL"])] for _, r in ic.iterrows()],
   w=[5.6, 1.1, 1.5, 1.4, 1.4, 1.6, 1.2, 1.3, 1.3], sz=7.5,
   nota="(1) Low-Vol devolvía datos vacíos en jul-2018 y dic-2018 y el modelo eliminaba esos meses de las 6 series, incluido el peor mes del período para las acciones. (2) El filtro de Sharpe de Momentum usaba la volatilidad de un mes en el backtest y de 12 meses en la operación. (3) Sensibilidad: contar el costo en compras y ventas. Ninguna corrección mueve los pesos más de 0,7 puntos.")
FIGURA("f6_robustez.png", "Figura 8. Robustez: Sharpe 2013-2026 de cada variante de parámetros (un cambio a la vez). Fuente: codigo/validacion.py.")
P(f"Robustez. Momentum y Low-Volatility son estables frente a sus parámetros (Sharpe entre {n_(rb[rb.Estrategia!='Commodities'].Sharpe.min())} y {n_(rb[rb.Estrategia!='Commodities'].Sharpe.max())}) y la regla vigente no es la mejor variante, lo que es evidencia en contra de sobreajuste. Momentum en commodities sí depende de sus umbrales y de la ampliación del universo de 3 a 5 ETF, que se decidió observando el backtest: se declara como sesgo de selección y explica su menor peso.")
sc = T["Sensibilidad_commodities"]
TB(["Universo de commodities", "Cartera: retorno anual", "Sharpe", "Máx. caída", "P(3 objetivos) histórico"],
   [[r["Universo"], p_(r["Cartera CAGR"], 2), n_(r["Cartera Sharpe"], 3), p_(r["Cartera máx. caída"]), p_(r["P(3 objetivos) histórico"])] for _, r in sc.iterrows()],
   w=[6.2, 2.6, 1.8, 2.3, 3.1],
   nota="Control del sesgo de selección: con el universo original de 3 ETF la cartera rinde 0,25 puntos menos al año y la probabilidad de cumplir los tres objetivos baja ~1 punto. La conclusión del IPS no depende de esa decisión.")
TB(["Cartera", "Sharpe 2013-2019 (dentro de muestra)", "Sharpe 2020-2026 (fuera de muestra)"],
   [[c, n_(wfv(c, "Dentro")), n_(wfv(c, "Fuera"))] for c in wf.Cartera.unique()], w=[7.4, 4.3, 4.3],
   nota="Walk-forward: los pesos se calibran solo con 2013-2019 y se evalúan en 2020-2026. Markowitz con medias históricas sobreajusta; Black-Litterman calibrado con la misma información mantiene el mejor desempeño fuera de muestra, lo que respalda su uso.")
P("Sesgos y limitaciones declarados:", b=None)
B(["Clasificación sectorial actual (no histórica) en el límite sectorial: sesgo de anticipación leve; afecta sobre todo antes de 2016 y a ~3% de posiciones sin clasificar.",
   "Precio faltante en el mes: se trata como 0% en esa posición.",
   "Commodities: universo ampliado mirando el backtest (sesgo de selección), controlado con el universo original.",
   "Montecarlo: bootstrap independiente (no captura regímenes ni autocorrelación); los supuestos prospectivos son propios, no pronósticos."])

# ================= 5. IMPLEMENTACIÓN =================
d.add_page_break(); H("5. Implementación en StockTrak (al 5-oct-2026)")
P("La cartera se implementó el 14-sep-2026 con los pesos aprobados. Decisiones relevantes durante la ejecución:")
B([("Rebalanceo de fin de septiembre: ", "Momentum se llevó a peso igual; Moderna se redujo de 12 a 5 acciones, asegurando ~USD 225 de ganancia, con un stop móvil sobre el costo para las restantes."),
   ("Low-Volatility: ", "se redujo utilities y real estate de 50% a ~29% del sleeve (salieron Realty Income y Duke Energy), por la sensibilidad a tasas observada; entraron PG, RSG y SNA siguiendo el ranking."),
   ("Petróleo: ", "se vendieron MPC, VLO y USO para reducir la exposición conjunta al petróleo; la señal de octubre confirmó la salida de USO."),
   ("Cobertura cambiaria: ", f"el 28-sep se contrató fuera de StockTrak un forward de venta de USD {n_(fc['Monto (USD)'],0)} a CLP {n_(fc['Precio forward (CLP por USD)'])} con vencimiento el 30-sep-2027 (sección 3.4)."),
   ("Operaciones: ", "~50 en las primeras tres semanas, en línea con la regla de 150 en 12 semanas. Las comisiones de la plataforma (~USD 10 por operación, ~USD 1.500 por las 150 exigidas) se tratan como costo operativo de la simulación y no entran en Black-Litterman ni en el Montecarlo.")])
P("Desviaciones respecto de la regla, documentadas:", b=None)
TB(["Fecha", "Sleeve", "Desviación", "Motivo / tratamiento"], [
    ["14-sep", "Commodities", "Compra de USO aunque al 31-ago ningún commodity calificaba", "La señal se recalculó con precios del 14-sep (día de la implementación). Se vendió el 2-oct; la señal de octubre confirmó su salida"],
    ["21-sep", "Low-Volatility", "Se reemplazaron BRK/B y MCD por AFL y FRT", "FRT entraba a la selección de la revisión del 18-sep (en lugar de O). AFL y las salidas de BRK/B y MCD no corresponden a la regla: desviación discrecional, se corrige en el rebalanceo de fin de octubre"],
    ["30-sep", "Low-Volatility", "Salen O y DUK; entran PG, RSG y SNA; se excluye MCD", "Reducir utilities y REITs (sensibles a tasas) de 50% a ~29% del sleeve; MCD excluida por deterioro de tendencia. Reemplazos en orden del ranking"],
    ["2-oct", "Momentum / Commodities", "Venta de MPC, VLO y USO", "Reducir la exposición conjunta al petróleo; MPC y VLO seguían en la señal (decisión de riesgo)"]], w=[1.5, 2.6, 5.4, 6.5], sz=7.5)
P("Momentum es el sleeve con mejor desempeño en vivo (≈ +3,7% desde el 14-sep frente a ≈ +2,4% de QMOM). La cartera total se ve afectada por la subida de la tasa a 10 años a 5,3%, que golpea al núcleo de renta fija larga (~30% de la cartera). Es el principal riesgo de corto plazo y está identificado en la sección 6.", it=False)
vc = AD["Vivo_por_clase"].set_index("Clase")
TB(["Clase", "Invertido el 14-sep", "Resultado (USD)", "Retorno Nexum", "Benchmark", "Retorno benchmark", "Diferencia"],
   [[k, u_(r["Invertido el 14-sep"]), n_(r["Resultado (USD)"], 0), p_(r["Retorno Nexum"], 2), r["Benchmark"], p_(r["Retorno benchmark"], 2), f"{n_(r['Diferencia (pp)'])} pp"] for k, r in vc.iterrows()],
   w=[3.4, 2.4, 2, 1.8, 3.2, 1.8, 1.6], sz=7.5,
   nota="Desde el 14-sep hasta el 6-oct (exports de StockTrak). El resultado incluye dividendos y comisiones de USD 10; los benchmarks parten de nuestro precio de entrada (o del cierre del 14-sep) con dividendos reinvertidos. La suma de los resultados cuadra con la pérdida total de la cuenta. Fuente: codigo/analisis_adicional.py.")
rvv, cmv = vc.loc["Renta variable EE.UU."], vc.loc["Commodities"]
P(f"Por clase de activo: la renta fija replica su benchmark, como corresponde a un núcleo pasivo; la renta variable queda {n_(-rvv['Diferencia (pp)'],1)} puntos bajo el S&P 500, en parte por las comisiones ({int(rvv['Operaciones'])} operaciones, USD {n_(10*rvv['Operaciones'],0)}) y en parte por el sesgo defensivo de Low-Volatility en un mercado al alza; commodities queda {n_(-cmv['Diferencia (pp)'],1)} puntos bajo su benchmark por la pérdida en USO, ya liquidado.")

# ================= 6. RIESGOS =================
H("6. Riesgos principales y mitigantes")
TB(["Riesgo", "Exposición", "Mitigante"], [
    ["Tasas de interés", "TLH + VCLT ≈ 31%; más Low-Vol en utilities/REITs", "Banda de rebalanceo; límite a utilities/REITs; revisión de la duración en la revisión anual"],
    ["Retorno de mercado menor al requerido", "Retorno esperado ≈ requerido", "Palancas acordadas: herencia y luego Villarrica; nunca Educación"],
    ["Concentración tecnológica / capital humano", "Empleo de Tomás en software", "Límite de 2 acciones por sector en el satélite; tecnología ~14% vs ~26% en la AGF"],
    ["Caídas abruptas de Momentum", "7% de la cartera, volatilidad ~24%", "Peso acotado, peso igual, stops de emergencia"],
    ["Tipo de cambio", "Objetivos en UF/CLP, activos en USD", "Forward de venta de USD 104.000 a un año (~70%, cerca de la cobertura de mínimo riesgo en pesos); cobertura natural; simulaciones en UF; reserva cambiaria de 2%"],
    ["Liquidez del forward", "Si el dólar sube, Nexum paga la compensación al vencimiento (sept-2027)", f"Se paga con SGOV y venta de activos en USD, que en ese escenario valen más en pesos; supera la reserva de 2% en {p_(fl['Probabilidad de pagar más que la reserva cambiaria (USD 3.000)'],0)} de los escenarios; valor de mercado informado mensualmente"],
    ["Empleo de Tomás", "Aportes condicionados a seguir empleado", "Escenario de 14 aportes en la TIR; fondo de emergencia fuera del mandato; seguro de vida e invalidez"]], w=[3.6, 5.6, 6.8])

# ================= 7. CONCLUSIÓN =================
H("7. Conclusión")
P(f"La estrategia Nexum cumple el objetivo prioritario —Educación— en prácticamente todos los escenarios, en USD y en UF. Villarrica y la herencia dependen del retorno que entregue el mercado: se cumplen holgadamente con retornos como los de 2013-2026 y con {p_(g('Nexum','Prosp','USD','P(3 objetivos)'),0)} de probabilidad conjunta bajo supuestos prudentes. Frente a la cartera actual de la AGF, Nexum reduce la concentración en EE.UU. y en tecnología, baja las caídas esperadas y mejora la probabilidad de éxito hacia adelante. La recomendación es mantener la asignación, revisar anualmente el Montecarlo con los gatillos de la sección 2.9 y acordar desde ya el orden de ajuste con la familia.")

# ================= REFERENCIAS =================
H("Referencias")
for ref in ["Ang, A., Hodrick, R., Xing, Y. y Zhang, X. (2006). The Cross-Section of Volatility and Expected Returns. Journal of Finance, 61(1), 259-299.",
 "Asness, C., Moskowitz, T. y Pedersen, L. (2013). Value and Momentum Everywhere. Journal of Finance, 68(3), 929-985.",
 "Baker, M., Bradley, B. y Wurgler, J. (2011). Benchmarks as Limits to Arbitrage: Understanding the Low-Volatility Anomaly. Financial Analysts Journal, 67(1), 40-54.",
 "Barroso, P. y Santa-Clara, P. (2015). Momentum Has Its Moments. Journal of Financial Economics, 116(1), 111-120.",
 "Black, F. y Litterman, R. (1992). Global Portfolio Optimization. Financial Analysts Journal, 48(5), 28-43.",
 "Blitz, D. y van Vliet, P. (2007). The Volatility Effect. Journal of Portfolio Management, 34(1), 102-113.",
 "Carhart, M. (1997). On Persistence in Mutual Fund Performance. Journal of Finance, 52(1), 57-82.",
 "Daniel, K. y Moskowitz, T. (2016). Momentum Crashes. Journal of Financial Economics, 122(2), 221-247.",
 "DeMiguel, V., Garlappi, L. y Uppal, R. (2009). Optimal Versus Naive Diversification. Review of Financial Studies, 22(5), 1915-1953.",
 "Erb, C. y Harvey, C. (2006). The Strategic and Tactical Value of Commodity Futures. Financial Analysts Journal, 62(2), 69-97.",
 "Faber, M. (2007). A Quantitative Approach to Tactical Asset Allocation. Journal of Wealth Management, 9(4), 69-79.",
 "Frazzini, A. y Pedersen, L. (2014). Betting Against Beta. Journal of Financial Economics, 111(1), 1-25.",
 "Grinold, R. y Kahn, R. (2000). Active Portfolio Management (2a ed.). McGraw-Hill.",
 "Haugen, R. y Heins, A. (1975). Risk and the Rate of Return on Financial Assets. Journal of Financial and Quantitative Analysis, 10(5), 775-784.",
 "He, G. y Litterman, R. (1999). The Intuition Behind Black-Litterman Model Portfolios. Goldman Sachs Investment Management Research.",
 "Jegadeesh, N. y Titman, S. (1993). Returns to Buying Winners and Selling Losers. Journal of Finance, 48(1), 65-91.",
 "Markowitz, H. (1952). Portfolio Selection. Journal of Finance, 7(1), 77-91.",
 "McLean, R. y Pontiff, J. (2016). Does Academic Research Destroy Stock Return Predictability? Journal of Finance, 71(1), 5-32.",
 "Miffre, J. y Rallis, G. (2007). Momentum Strategies in Commodity Futures Markets. Journal of Banking & Finance, 31(6), 1863-1886.",
 "Moskowitz, T., Ooi, Y. y Pedersen, L. (2012). Time Series Momentum. Journal of Financial Economics, 104(2), 228-250."]:
    p = d.add_paragraph(ref); p.paragraph_format.left_indent = Cm(0.6); p.paragraph_format.first_line_indent = Cm(-0.6); p.runs[0].font.size = Pt(8.5)

# ================= ANEXOS =================
d.add_page_break(); H("Anexo A. Bitácora de auditoría del modelo anterior")
TB(["Gravedad", "Hallazgo", "Corrección"], [
    ["Alta", "Fórmulas sin valores guardados en el Excel", "Modelo v2 recalculado y guardado en Excel"],
    ["Alta", "Mezcla de dos arquitecturas (calce LDI de Educación vs cartera única) y notas 'PENDIENTE'", "Solo cartera única; textos depurados"],
    ["Alta", "Referencias a Betting Against Beta (BAB_EQ)", "Eliminadas; la estrategia es Low-Volatility"],
    ["Alta", "Meses jul-2018 y dic-2018 eliminados de las 6 series por un dato vacío de Low-Vol", "Ventana completa de 164 meses"],
    ["Alta", "Filtro de Sharpe de Momentum con volatilidad de 1 mes en el backtest y 12 meses en la operación", "Una sola regla: 12 meses"],
    ["Media", "Columna π desplazada una fila en Black-Litterman; μ_BL y pesos pegados como valores", "Fórmulas matriciales vivas (MMULT, MINVERSE)"],
    ["Media", "Benchmarks distintos entre hojas", "Un benchmark invertible por sleeve"],
    ["Media", "Universo de commodities ampliado mirando el backtest", "Declarado y controlado"],
    ["Baja", "Métricas de la misma estrategia con distintas convenciones", "Una convención: exceso sobre T-Bills"]], w=[1.8, 8.4, 5.8])
H("Anexo B. Preguntas anticipadas para la defensa")
for q, a in [
 ("¿Por qué ampliaron el universo de commodities de 3 a 5 ETF después de ver el backtest?",
  f"Para diversificar entre complejos de commodities: metales preciosos, energía y agrícolas, más metales industriales (plata y cobre). Reconocemos que la elección de SLV y CPER se hizo después de ver el backtest; por eso lo declaramos como sesgo de selección y lo controlamos. Con el universo original de 3 ETF la cartera rinde 0,25 puntos menos al año, el Sharpe baja de {n_(sc.iloc[0]['Cartera Sharpe'])} a {n_(sc.iloc[1]['Cartera Sharpe'])} y la probabilidad de los tres objetivos de {p_(sc.iloc[0]['P(3 objetivos) histórico'])} a {p_(sc.iloc[1]['P(3 objetivos) histórico'])}. La conclusión no depende de esa decisión, y es el sleeve con menor peso (6,1%) justamente por ser el más frágil."),
 ("¿Por qué Villarrica tiene prioridad sobre la herencia, si la herencia es el monto mayor?",
  "Porque la herencia no tiene fecha rígida y es un objetivo de riqueza terminal a 50 años: por diseño absorbe la variabilidad de los resultados. Villarrica tiene fecha (la jubilación) y compromete además UF 15.000 de la venta de la casa. Es el orden del enunciado y fue validado con el criterio de flexibilidad. Las palancas siguen ese mismo orden: primero se ajusta la herencia, luego Villarrica, nunca Educación."),
 ("¿Por qué la probabilidad de cumplir los tres objetivos es solo 46,5% en el escenario prospectivo?",
  "Porque con supuestos prudentes el retorno real esperado (~4,6%) apenas iguala al requerido (4,56%). Lo presentamos con transparencia en vez de mostrar solo el 96% histórico. Educación está asegurada en todos los escenarios; para Villarrica y la herencia se acordaron palancas que elevan la probabilidad a ~75%."),
 ("¿Por qué USD como moneda funcional si las necesidades del cliente están en UF y CLP?",
  "Todo el universo de inversión cotiza en USD. El peso se deprecia cuando caen los mercados (cobertura natural) y el ahorro en USD diversifica el riesgo país de una familia cuyo capital humano y vivienda están en Chile. Las simulaciones se presentan también en UF, y el riesgo cambiario de corto plazo se cubre parcialmente con un forward."),
 ("Si el perfil excluye derivados, ¿por qué firmaron un forward?",
  f"El perfil excluye derivados complejos, apalancamiento y especulación. Un forward de monedas es el derivado más simple, se usa solo para cubrir y el monto es menor que la cartera, así que no apalanca. Cubre {p_(fc['Cobertura sobre el valor al 28-sep'],0)} de la cartera: más cobertura no reduce el riesgo en pesos, porque el peso ya se deprecia cuando caen los mercados. Su costo es bajo ({p_(-fc['Puntos como % del spot (≈ tasa CLP − tasa USD)'],2)} del monto) y su riesgo es de liquidez: si el dólar sube hay que pagar la compensación, pero en ese escenario la cartera vale más en pesos."),
 ("¿Contra qué se evalúa cada clase de activo?",
  f"Renta variable contra el S&P 500, renta fija larga contra el Bloomberg U.S. Long Government/Credit Index (el que sigue el ETF BLV), commodities contra la mezcla de sus 5 ETF y la reserva contra T-Bills. Frente a ese benchmark, Nexum rindió {p_(bkv('2016-2026','Cartera Nexum','CAGR'))} vs {p_(bkv('2016-2026','Benchmark por clase','CAGR'))} en 2016-2026, con menos volatilidad y caídas más bajas: el satélite de renta variable baja el riesgo, no busca superar al índice en un mercado alcista."),
 ("¿Por qué no usan Markowitz si tiene mayor Sharpe?",
  "Porque ese Sharpe es dentro de muestra. En la prueba fuera de muestra (calibrar con 2013-2019 y evaluar 2020-2026), Markowitz cae a 0,45, mientras que Black-Litterman calibrado con la misma información logra 0,65."),
 ("¿El modelo que presentan es el mismo que operan en StockTrak?",
  "Sí. Los pesos implementados son los de Black-Litterman y las reglas de las estrategias son las mismas del backtest. Las desviaciones discrecionales están documentadas en la sección 5 con fecha y motivo.")]:
    P(a, b=q + " ")
H("Anexo C. Reproducibilidad")
B(["codigo/config.py: todos los parámetros. codigo/estrategias.py: backtests. codigo/portafolio.py: Markowitz, Black-Litterman, benchmark y métricas.",
   "codigo/objetivos.py: flujos y TIR. codigo/montecarlo.py: simulación. codigo/validacion.py: robustez y walk-forward.",
   "codigo/run_all.py corre todo; codigo/excel_modelo.py genera el Excel; codigo/figuras.py e informe.py, este documento; codigo/senales.py, las señales de operación.",
   "codigo/analisis_adicional.py: benchmark por clase de activo, resultado en vivo por clase, forward USD/CLP, bandas de rebalanceo y activos adicionales (resultados/analisis_adicional.xlsx).",
   "La versión portada de los backtests reproduce exactamente los resultados del modelo anterior (diferencia máxima 10⁻¹⁶) antes de aplicar las correcciones."])
out = os.path.join(BASE, "informe", "Informe_Final_Nexum.docx"); d.save(out); print("OK", out)
