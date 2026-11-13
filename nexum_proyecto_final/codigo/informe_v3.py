"""Informe IPS + Estrategia de Inversión, versión 3 (post pre-defensa). Punto de partida para el informe final.

Incorpora la retroalimentación P2 y las respuestas del profesor guía: moneda funcional CLP, metas evaluadas en su
moneda, benchmark de EE.UU. fijado ex-ante con referencia global, tracking error con mínimo y máximo, costos de
StockTrak (USD 10 por orden) y pool completo de métricas. Lee resultados/*.pkl y *.csv (run_all.py,
analisis_adicional.py, costos_stocktrak.py, palancas_uf.py). Salida: ../../entregables/Informe_Nexum_v3.docx
"""
import os
import pandas as pd
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from config import RESULTADOS

R = RESULTADOS
T = pd.read_pickle(os.path.join(R, "estado.pkl"))["T"]; A = pd.read_pickle(os.path.join(R, "adicional.pkl"))
C = pd.read_pickle(os.path.join(R, "costos_stocktrak.pkl")); PU = pd.read_csv(os.path.join(R, "palancas_uf.csv"))
SALIDA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "entregables", "Informe_Nexum_v3.docx"))

def p_(x, d=1): return f"{x * 100:.{d}f}%".replace(".", ",")
def n_(x, d=0): return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")

doc = Document()
st = doc.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(11.5)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
for s in doc.sections: s.left_margin = s.right_margin = Cm(2.5); s.top_margin = s.bottom_margin = Cm(2.2)

def H(t, l=1):
    h = doc.add_heading(t, level=l)
    for r in h.runs: r.font.name = "Times New Roman"; r.font.color.rgb = RGBColor(0x14, 0x24, 0x4A)
def P(t, it=False):
    q = doc.add_paragraph(); q.paragraph_format.space_after = Pt(6); q.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = q.add_run(t); r.italic = it; return q
def PB(partes):
    q = doc.add_paragraph(); q.paragraph_format.space_after = Pt(6); q.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for b, t in partes:
        r = q.add_run(t); r.bold = b
def L(items):
    for it in items:
        q = doc.add_paragraph(style="List Bullet"); q.paragraph_format.space_after = Pt(2)
        if isinstance(it, tuple): q.add_run(it[0]).bold = True; q.add_run(it[1])
        else: q.add_run(it)
def PEND(t):
    q = doc.add_paragraph(); r = q.add_run("[PENDIENTE] " + t); r.bold = True; r.font.color.rgb = RGBColor(0xB0, 0x3A, 0x2E)
def sombra(cell, color):
    tcPr = cell._tc.get_or_add_tcPr(); sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), color); tcPr.append(sh)
def TB(enc, filas, nota=None, anchos=None):
    t = doc.add_table(rows=1, cols=len(enc)); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, e in enumerate(enc):
        c = t.rows[0].cells[i]; c.text = ""; r = c.paragraphs[0].add_run(str(e)); r.bold = True; r.font.size = Pt(9.5); sombra(c, "E4E3DF")
    for f in filas:
        cs = t.add_row().cells
        for i, v in enumerate(f):
            cs[i].text = ""; r = cs[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(9.5)
    if anchos:
        for row in t.rows:
            for i, w in enumerate(anchos): row.cells[i].width = Cm(w)
    if nota:
        q = doc.add_paragraph(); r = q.add_run(nota); r.italic = True; r.font.size = Pt(9)
    else: doc.add_paragraph()

fac = T["Factibilidad"].set_index("Concepto")["Valor"]; tir = T["TIR"].set_index("Escenario")["TIR real requerida"]
mc = T["Montecarlo"]; g = lambda car, esc, mon, col: mc[(mc.Cartera == car) & (mc.Escenario.str.startswith(esc)) & (mc.Moneda == mon)][col].iloc[0]
cs = C["metricas"]; c_ = lambda per, costo, mon, col: cs[(cs["Período"] == per) & (cs.Costo.str.startswith(costo)) & (cs.Moneda == mon)][col].iloc[0]
es = C["estrategias"]; e_ = lambda k, costo: es[(es.Estrategia == k) & (es.Costo == costo)]
te = T["Tracking_error"].set_index("Concepto")["Valor"]; met = T["Metricas"]
pl = T["Palancas"].set_index("Palanca (prospectivo, USD)"); pu = PU.set_index("Palanca")

# ------------------------------------------------------------------ Portada
q = doc.add_paragraph(); q.alignment = WD_ALIGN_PARAGRAPH.CENTER; r = q.add_run("\n\nNexum Financial Advisors\n"); r.bold = True; r.font.size = Pt(20)
q = doc.add_paragraph(); q.alignment = WD_ALIGN_PARAGRAPH.CENTER; r = q.add_run("Investment Policy Statement e Informe de Estrategia de Inversión\nFamilia Allende-Cunich"); r.font.size = Pt(15)
q = doc.add_paragraph(); q.alignment = WD_ALIGN_PARAGRAPH.CENTER; q.add_run("Iannello · Lillo · Morales · Salah · Torres\nExperiencia de Simulación en Finanzas · ESF 2026-2 · Universidad Adolfo Ibáñez\nVersión 3 (posterior a la pre-defensa) · borrador de trabajo")
P("Uso de inteligencia artificial: el equipo usó herramientas de IA para buscar información, revisar redacción y escribir "
  "código en Python (backtesting, Black-Litterman y Montecarlo). Todos los cálculos se pueden reproducir con el código y el "
  "Excel adjuntos, y cada cifra de este documento fue revisada por el equipo.", it=True)
P("Nota para el equipo: este borrador reemplaza la versión anterior del documento, que mezclaba la estrategia de la Parte I "
  "(cartera pasiva 65,6% / activa 34,4%, Betting Against Beta, benchmark ACWI y tasa de la Fed) con la estrategia que "
  "efectivamente se opera en StockTrak. Las marcas [PENDIENTE] indican lo que falta completar con datos al cierre del "
  "trading o con decisiones del grupo. El texto está escrito para que cada integrante lo revise y lo reescriba con sus palabras.", it=True)
doc.add_page_break()

# ================================================================== PARTE I · IPS
H("Parte I · Investment Policy Statement", 1)
P("Este IPS es el acuerdo entre Nexum Financial Advisors (el asesor) y María Ignacia Cunich y Tomás Allende (los clientes). "
  "Define los objetivos, la tolerancia al riesgo, las restricciones y las reglas con que se administra la cartera, y es la "
  "referencia para evaluar cada decisión de inversión y su desempeño.")

H("1. Los clientes y el asesor", 2)
P("María Ignacia (40 años, abogada especialista en derecho comercial en una empresa de consumo masivo) y Tomás (46 años, "
  "ingeniero en computación con 20 años en una empresa de software) viven en Santiago con sus hijos Vicente (4) y Emilia (2). "
  "Su nivel de educación financiera es medio y no tienen experiencia con derivados sofisticados ni criptoactivos.")
P("El asesor actúa como fiduciario bajo el Código de Ética y los Estándares de Conducta Profesional del CFA Institute y la "
  "normativa de la CMF. Es responsable de proponer la asignación, seleccionar instrumentos, ejecutar y rebalancear, "
  "monitorear el riesgo e informar a los clientes de forma periódica y transparente.")

H("2. Patrimonio y flujos", 2)
TB(["Activo o flujo", "Monto", "Observación"], [
    ["Capital a invertir", "USD 150.000", "Hoy en fondos mutuos de una AGF chilena (85% acciones: 90% S&P 500 y 10% MSCI EAFE; 15% bonos globales)"],
    ["Aportes", "USD 10.000 cada abril", "Hasta que Tomás cumpla 65 años (19 aportes), sujetos a que haya estado empleado el año anterior"],
    ["Casa en Santiago", "UF 30.000", "Fuera del mandato. Su venta aportará UF 15.000 a la compra de Villarrica, como indica el caso"]],
   anchos=[4, 3.5, 8.5])

H("3. Perfil de riesgo", 2)
P("El perfil se determinó con tres factores, siguiendo el marco del CFA Institute y la guía de perfilamiento de la CMF:")
L([("Capacidad de riesgo alta. ", "El horizonte es largo (hasta 50 años), no hay retiros hasta el año 14 y los ingresos son estables."),
   ("Disposición al riesgo media. ", "En el cuestionario de Grable y Lytton (1999), de 13 ítems, la pareja obtiene 30 puntos en un rango de 13 a 47 "
    "(Anexo 1). El simulador de perfil de Banchile Inversiones también entrega perfil moderado, con hasta 60% en renta variable."),
   ("Capital humano expuesto a tecnología. ", "El ingreso de Tomás depende de la industria de software: si el sector cae, es más probable "
    "que pierda su empleo justo cuando la cartera cae. Por eso la cartera limita la exposición adicional a tecnología.")])
P("Conclusión: perfil moderado. En la práctica esto significa entre 60% y 65% en renta variable, una volatilidad anual de 10% a 12% "
  "medida en pesos y una caída máxima tolerable de 25% (sección 7).")

H("4. Objetivos de inversión", 2)
P("Cada objetivo se evalúa en la moneda en que el caso lo define, no en dólares. Los montos están en dinero de hoy.")
TB(["Prioridad", "Objetivo", "Monto (dinero de hoy)", "Año", "Moneda de evaluación", "Flexibilidad"], [
    ["1", "Educación de Vicente y Emilia (5 cuotas anuales cada uno)", "CLP 65 MM por hijo = UF 1.591 por hijo (UF 318 por cuota)", "14–20", "UF", "Rígida: no se posterga"],
    ["2", "Casa en Lago Villarrica (aporte de la cartera)", "UF 10.500 (+ UF 15.000 de la venta de la casa)", "25", "UF", "Postergable o reducible"],
    ["3", "Herencia", "USD 250.000 por hijo (USD 500.000)", "50", "USD reales", "Variable de ajuste"]],
   nota="Conversiones de referencia al 11-ago-2026: dólar observado CLP 911,77 y UF CLP 40.846. Educación en UF = CLP 65.000.000 / 40.846. "
        "Entre los años 16 y 18 se pagan las dos carreras a la vez: es el período de mayor necesidad de liquidez.")
P("Orden de prioridad: Educación es la única meta que no admite sustitución ni postergación. Villarrica tiene fecha (la jubilación) "
  "pero el propio caso admite ajustar el monto o la ubicación. La herencia, a 50 años y sin fecha rígida, es la que absorbe la "
  "variabilidad de los resultados. Por eso, si hay que ajustar, primero se ajusta la herencia, luego Villarrica y nunca Educación.")

H("5. Retorno requerido y factibilidad", 2)
P(f"El retorno requerido es la TIR real que iguala lo que entra a la cartera (USD 144.000 invertidos, es decir, USD 150.000 menos la "
  f"reserva de 4%, y 19 aportes de USD 10.000) con lo que sale (Educación, Villarrica y herencia en su año de pago). Con tipo de "
  f"cambio real constante, la TIR requerida es {p_(fac['TIR requerida'], 2)} real anual.")
P(f"Prueba de factibilidad: a la tasa real libre de riesgo de 2,5% (bono del Tesoro a 10 años de 4,62% menos la inflación objetivo "
  f"de la Fed de 2%), el valor presente de los recursos es USD {n_(fac['VP recursos (capital + aportes)'])} y el de los objetivos "
  f"USD {n_(fac['VP objetivos'])}: una cobertura de {n_(fac['Cobertura (recursos / objetivos)'], 2)}x. Invirtiendo sin riesgo el plan no "
  f"se financia, así que la cartera debe ganar una prima por riesgo. Villarrica es la meta que más pesa en esa exigencia "
  f"({p_(fac['Peso VP Villarrica'], 0)} del valor presente de los objetivos), seguida de Educación ({p_(fac['Peso VP Educación'], 0)}) "
  f"y la herencia ({p_(fac['Peso VP Herencia'], 0)}).")
TB(["Escenario", "TIR real requerida"], [[i, p_(v, 2)] for i, v in tir.items()],
   nota="Las tres últimas filas son las palancas de ajuste que se presentan a la familia (Parte II, sección 7).", anchos=[11, 4])
P("Un cambio en el tipo de cambio real modifica la TIR medida en pesos: si el peso se aprecia en términos reales, la Educación y "
  "Villarrica cuestan más dólares y el requerimiento sube. Ese riesgo no se ve en la TIR; se mide en el Montecarlo con las metas "
  "en UF (Parte II, sección 7).")

H("6. Horizonte de inversión", 2)
TB(["Objetivo", "Horizonte", "Clasificación", "Implicancia"], [
    ["Educación", "14 a 20 años", "Largo plazo", "Desde el año 11 se cubre el riesgo cambiario de las cuotas y se reduce el riesgo de los recursos comprometidos"],
    ["Villarrica", "25 años", "Muy largo plazo", "Admite volatilidad; se revisa la palanca de monto 5 años antes"],
    ["Herencia", "50 años", "Muy largo plazo", "Absorbe la variabilidad; prioriza crecimiento"]], anchos=[3, 3, 3, 7])

H("7. Tolerancia al riesgo y límites", 2)
P("Los límites siguientes son parte del IPS. Si alguno se supera, se activa la revisión extraordinaria de la sección 13.")
TB(["Parámetro", "Límite", "Por qué"], [
    ["Renta variable", "60% a 65%", "Perfil moderado; coherente con el simulador de Banchile (hasta 60%) y la capacidad alta"],
    ["Núcleo pasivo", "60% a 70% de la cartera", "El resto (30% a 40%) son estrategias activas sistemáticas"],
    ["Volatilidad anual, medida en CLP", "10% a 12%", "Rango de un perfil moderado; se cumple con la cobertura cambiaria (Parte II, sección 2)"],
    ["Caída máxima tolerable", "25%", "Pérdida que la familia declara poder soportar sin cambiar de estrategia"],
    ["Tracking error ex-ante", "Mínimo 2%, objetivo 3%, máximo 4%", "El mínimo asegura una gestión activa real; el máximo limita el riesgo activo (Parte II, sección 5)"],
    ["Probabilidad de financiar Educación", "Al menos 90%", "Meta rígida; se mide en UF en el Montecarlo prudente"],
    ["Reserva de liquidez", "4% en letras del Tesoro (SGOV)", "Fondo de emergencia y respaldo de las compensaciones del forward"]],
   anchos=[4.5, 4, 7.5])

H("8. Restricciones", 2)
L([("Liquidez: ", "sin retiros hasta el año 14; reserva de 4% fuera de la asignación estratégica."),
   ("Instrumentos permitidos: ", "ETF y acciones transadas en EE.UU., disponibles en StockTrak. Se excluyen las ventas cortas, el "
    "apalancamiento, las compras a margen y los criptoactivos. Los derivados se limitan a forwards o swaps de cobertura con bancos "
    "regulados, explicados y aceptados por los clientes (CFA, Estándar III.C, idoneidad)."),
   ("Operación: ", "la cartera se ejecuta en StockTrak con comisión de USD 10 por orden y debe registrar al menos 150 transacciones "
    "en las semanas de trading (promedio mínimo de 5 por semana)."),
   ("Ética: ", "los clientes no declaran exclusiones sectoriales. Rige el Código de Ética del CFA Institute.")])

H("9. Cumplimiento normativo (CMF y Ley 19.913)", 2)
TB(["Proceso", "Qué hace el asesor"], [
    ["Conozca a su cliente", "Identificación, verificación y perfil documentado en este IPS; actualización anual"],
    ["Origen de fondos", "Respaldo del capital (ahorros en fondos mutuos de la AGF) y de los aportes (rentas del trabajo de Tomás)"],
    ["Personas expuestas políticamente y listas de sanciones", "Revisión al inicio; debida diligencia reforzada si hay coincidencia"],
    ["Monitoreo", "Revisión mensual de operaciones inusuales respecto del perfil"],
    ["Reporte a la UAF", "Reporte de operación sospechosa con deber de reserva"],
    ["Registros", "Conservación de registros por 5 años"]], anchos=[5, 11])

H("10. Moneda funcional", 2)
P("La moneda funcional es el peso chileno (CLP): los clientes viven en Chile y sus metas están en pesos y UF. El rendimiento, "
  "el riesgo, el benchmark y los resultados se miden en CLP. El dólar es la moneda de los instrumentos: el universo de inversión "
  "son ETF y acciones de EE.UU., y el retorno en pesos es el retorno en dólares más la variación del dólar observado. "
  "Las metas se evalúan en su propia moneda: Educación y Villarrica en UF y la herencia en USD reales, convertida a pesos al tipo "
  "de cambio de cada escenario.")

H("11. Asignación estratégica", 2)
asg = T["Asignacion"]
TB(["Componente", "Instrumento o estrategia", "Clase de activo", "Peso"], [
    ["Núcleo pasivo", "S&P 500 (SPY)", "Renta variable EE.UU.", "37,9%"],
    ["Núcleo pasivo", "Tesoro EE.UU. 10–20 años (TLH)", "Renta fija larga", "16,9%"],
    ["Núcleo pasivo", "Corporativos de largo plazo (VCLT)", "Renta fija larga", "14,6%"],
    ["Satélite activo", "Low-Volatility (10 acciones del S&P 500)", "Renta variable EE.UU.", "17,5%"],
    ["Satélite activo", "Momentum en acciones (7 acciones)", "Renta variable EE.UU.", "7,1%"],
    ["Satélite activo", "Momentum en commodities (ETF)", "Commodities", "6,1%"],
    ["", "Total", "Renta variable 62,5% · renta fija 31,5% · commodities 6,1%", "100%"]],
   nota="Pesos sobre el 96% invertido; la reserva de 4% en SGOV queda fuera de la asignación. Núcleo 69,4% y satélites 30,6%.", anchos=[3, 5.5, 5.5, 2])
P("Los pesos salen de un modelo Black-Litterman: el punto de partida es una cartera de paridad de riesgo (peso inverso a la "
  "volatilidad) y sobre ella se incorporan dos vistas del equipo: el S&P 500 rinde 6% anual y Low-Volatility rinde 2 puntos más "
  "que los commodities. La optimización maximiza el Sharpe con el núcleo restringido a entre 60% y 70%.")
PEND("Decidir si el núcleo baja a 60% (satélites 40%), dentro del rango que ya permite este IPS, para responder a la crítica de gestión "
     "casi pasiva. Antes de decidirlo hay que medir el efecto en el tracking error y en los costos (Parte II, secciones 5 y 6).")

H("12. Criterios de selección y rebalanceo", 2)
TB(["Componente", "Regla de selección", "Revisión"], [
    ["Núcleo", "ETF líquidos y de bajo costo que replican su índice", "Bandas de ±5 puntos por activo"],
    ["Low-Volatility", "Las 10 acciones del S&P 500 con menor volatilidad a 12 meses; precio ≥ USD 5; liquidez ≥ USD 5 MM diarios; "
     "máximo 2 por sector; utilities + REITs ≤ 30%; pesos iguales", "Mensual; bandas de ±2 puntos"],
    ["Momentum en acciones", "Filtros: retorno a 3, 6 y 12 meses > 0%, 5% y 10%; precio sobre su media de 200 días; Sharpe a 12 meses ≥ 0,5; "
     "liquidez ≥ USD 5 MM. Orden por 50% retorno a 6 meses + 50% a 12 meses. 7 acciones, máximo 2 por sector", "Semanal; una acción se mantiene mientras siga en el top 25"],
    ["Momentum en commodities", "ETF de oro, plata, cobre, petróleo y agrícolas con tendencia a 3, 6 y 12 meses y precio sobre su media de 200 días; "
     "pesos iguales; si ninguno califica, letras del Tesoro", "Mensual"]], anchos=[3.5, 9, 3.5])
P("Las ventas responden a la señal de cada estrategia, no al precio: una caída de 15% en una posición es una alerta que obliga a "
  "revisar la tesis, no una venta automática. Los aportes de abril se invierten primero en los activos bajo su peso objetivo, para "
  "rebalancear sin vender.")

H("13. Revisión y control", 2)
L(["Reporte mensual a los clientes con el valor, el rendimiento en CLP, las transacciones y la comparación con el benchmark.",
   "Revisión anual del IPS y del Montecarlo con datos actualizados.",
   "Revisión extraordinaria si: la probabilidad de Educación cae bajo 90%; la cartera cae más de 15% desde su máximo; el tracking "
   "error sale del rango de 2% a 4%; Tomás pierde su empleo; nace un tercer hijo o cambia algún objetivo.",
   "Todo cambio de asignación o de benchmark se documenta con fecha y motivo y se aplica solo hacia adelante."])

H("14. Firmas", 2)
P("\n______________________________            ______________________________\nMaría Ignacia Cunich                                   Tomás Allende\n\nFecha: ____________")
doc.add_page_break()

# ================================================================== PARTE II · Estrategia
H("Parte II · Informe de Estrategia de Inversión", 1)
H("Resumen ejecutivo", 2)
P(f"La familia necesita una rentabilidad real de {p_(fac['TIR requerida'], 2)} anual para financiar sus tres objetivos. Nexum propone una "
  f"cartera core-satélite: un núcleo pasivo de 69,4% (S&P 500 y bonos largos del Tesoro y corporativos) y tres estrategias activas "
  f"sistemáticas, Low-Volatility, Momentum en acciones y Momentum en commodities, que suman 30,6%. La cartera se mide en pesos y "
  f"cubre cerca de 70% de su exposición al dólar con un forward.")
P(f"En el backtest 2016–2026, con la comisión real de StockTrak, la cartera rinde {p_(c_('2016-2026', 'USD 10', 'CLP', 'CAGR Nexum'))} anual "
  f"en pesos frente a {p_(c_('2016-2026', 'USD 10', 'CLP', 'CAGR benchmark'))} del benchmark, con menor volatilidad "
  f"({p_(c_('2016-2026', 'USD 10', 'CLP', 'Vol. Nexum'))} vs {p_(c_('2016-2026', 'USD 10', 'CLP', 'Vol. benchmark'))}) y menor caída máxima "
  f"({p_(c_('2016-2026', 'USD 10', 'CLP', 'Máx. caída Nexum'))} vs {p_(c_('2016-2026', 'USD 10', 'CLP', 'Máx. caída benchmark'))}). "
  f"En el Montecarlo prudente, con cada meta en su moneda, Educación se financia en {p_(pu.loc['Plan actual', 'P(Educación)'])} de los escenarios, "
  f"Villarrica en {p_(pu.loc['Plan actual', 'P(Villarrica)'])} y las tres metas en {p_(pu.loc['Plan actual', 'P(3 objetivos)'])}. "
  f"Si la familia acepta las dos palancas de ajuste, la probabilidad conjunta sube a {p_(pu.loc['Ambas', 'P(3 objetivos)'])}.")

H("1. Estrategia de inversión y evidencia", 2)
P("El caso pide una estrategia mixta, con apuestas calculadas y no especulativas. La estructura core-satélite responde a eso: "
  "el núcleo captura las primas de mercado a bajo costo y los satélites concentran el riesgo activo en tres anomalías documentadas, "
  "con reglas fijadas antes de operar.")
TB(["Componente", "Qué hace", "Evidencia", "Retorno real esperado", "Volatilidad histórica"], [
    ["S&P 500", "Prima de mercado", "CAPM; Bodie, Kane y Marcus", "5,0%", p_(asg.iloc[0]['Volatilidad anual'])],
    ["Tesoro 10–20 años", "Prima por plazo; refugio en crisis", "Correlación negativa con acciones en caídas", "2,6%", p_(asg.iloc[1]['Volatilidad anual'])],
    ["Corporativos largos", "Prima de crédito", "Grado de inversión", "3,2%", p_(asg.iloc[2]['Volatilidad anual'])],
    ["Low-Volatility", "Menos caída con retorno similar", "Anomalía de baja volatilidad: Ang et al. (2006); Frazzini y Pedersen (2014)", "4,5%", p_(asg.iloc[5]['Volatilidad anual'])],
    ["Momentum en acciones", "Crecer con las tendencias", "Jegadeesh y Titman (1993)", "5,5% antes de costos", p_(asg.iloc[4]['Volatilidad anual'])],
    ["Momentum en commodities", "Diversificar", "Moskowitz, Ooi y Pedersen (2012)", "2,0%", p_(asg.iloc[3]['Volatilidad anual'])]],
   nota="Retornos esperados: tasa real libre de riesgo de 2,5% más primas recortadas frente a la historia, porque las primas de los factores "
        "caen después de publicarse (McLean y Pontiff, 2016). Volatilidad histórica 2013–2026 en USD.", anchos=[3, 3, 5, 2.5, 2.5])
P("Por qué Low-Volatility y no Betting Against Beta: la estrategia de Frazzini y Pedersen se apalanca en las acciones de beta baja y "
  "vende en corto las de beta alta. El perfil excluye apalancamiento y ventas cortas, así que Nexum captura la misma anomalía solo con "
  "posiciones largas.")
P("Alternativas descartadas: Markowitz histórico (se sobreajusta: Sharpe de 1,46 dentro de muestra y 0,45 fuera de muestra, frente a "
  "0,65 de Black-Litterman); pesos iguales (pone 17% en commodities, fuera del perfil); y la cartera actual de la AGF, que tiene 85% "
  "en acciones, más que el máximo de 65% del perfil.")

H("2. Moneda funcional y cobertura cambiaria", 2)
rc = T["Riesgo_cambiario"].set_index("Indicador")["Valor"]; fs = A["Forward_simulacion"]
f_ = lambda med, car, col: fs[(fs["Medido en"].str.startswith(med)) & (fs.Cartera == car)][col].iloc[0]
P(f"Medida en pesos, la cartera hereda la volatilidad del dólar ({p_(rc['Volatilidad anual USD/CLP'])} anual). Hay una cobertura natural: el peso "
  f"se deprecia cuando caen las bolsas (correlación de {n_(rc['Correlación S&P 500 vs. Δ USD/CLP'], 2)}), y en el 10% de peores meses del S&P 500 la "
  f"cartera cae {p_(rc['Retorno cartera en USD (peores meses)'])} en dólares pero solo {p_(rc['Retorno cartera en CLP (peores meses)'])} en pesos. "
  f"Aun así, sin cobertura la volatilidad en pesos queda sobre el límite del IPS.")
P("El 28-sep-2026 Nexum contrató un forward con el Banco de Chile: vende USD 104.000 a CLP 963,08 por dólar (spot de 967,32 menos 4,24 puntos), con "
  "vencimiento el 30-sep-2027, y se renueva cada año. Cubre cerca de 70% de la cartera. El costo es 0,44% del monto (≈ USD 456).")
TB(["Medido en CLP, a 12 meses", "Sin cobertura", "Con el forward"], [
    ["Volatilidad", p_(f_("CLP", "Sin cobertura", "Volatilidad")), p_(f_("CLP", "Con el forward", "Volatilidad"))],
    ["Peor 5%", p_(f_("CLP", "Sin cobertura", "Peor 5%")), p_(f_("CLP", "Con el forward", "Peor 5%"))],
    ["Probabilidad de perder más de 10%", p_(f_("CLP", "Sin cobertura", "P(pérdida > 10%)")), p_(f_("CLP", "Con el forward", "P(pérdida > 10%)"))]],
   nota="Simulación de 20.000 escenarios de 12 meses con meses reales 2013–2026 (cartera y dólar sorteados juntos).", anchos=[7, 4, 4])
P("Por qué cerca de 70% y no 100%: como el peso se deprecia en las crisis, cubrir todo eliminaría esa protección natural. La razón de "
  "cobertura que minimiza la volatilidad en pesos está cerca de 75%.")
P("Liquidez: si el dólar sube, Nexum paga la compensación al vencimiento (51% de los escenarios). La reserva de 4% (USD 6.000) alcanza hasta un dólar "
  "de CLP 1.022 y se supera en 33% de los escenarios. En el peor 5% el pago es de unos USD 19.500, que se financia con SGOV y venta de activos en "
  "dólares, que en ese escenario valen más en pesos.")
P("Cobertura de la UF para Educación (propuesta): el forward fija pesos, pero la Educación se paga en UF. A partir del año 11 (2037) se propone un swap "
  "peso/UF: Nexum paga pesos a tasa fija y recibe UF en cada fecha de cuota (≈ UF 318 por cuota). Así el dólar y la inflación quedan cubiertos por "
  "separado. Requiere modificar el IPS y el consentimiento informado de la familia.")

H("3. Benchmark", 2)
P("El benchmark oficial es compuesto, invertible y se fijó antes de operar. Usa los mismos pesos por clase que la cartera y se rebalancea "
  "mensualmente. Se expresa en pesos con el dólar observado, igual que la cartera.")
TB(["Clase", "Peso", "Índice", "Instrumento invertible"], [
    ["Renta variable EE.UU.", "62,4%", "S&P 500", "SPY"],
    ["Renta fija larga EE.UU.", "31,5%", "Bloomberg U.S. Long Government/Credit", "50% TLH + 50% VCLT (BLV no está en la base de datos)"],
    ["Commodities", "6,1%", "Bloomberg Commodity Index TR", "DJP"],
    ["Reserva (fuera de la asignación)", "4%", "T-Bills 0–3 meses", "SGOV"]], anchos=[4, 1.5, 5, 5.5])
P("Por qué un benchmark de EE.UU.: el caso exige un benchmark acorde al universo de activos, y el universo de inversión son instrumentos de "
  "EE.UU. Como verificación, se comparó con una referencia global con los mismos pesos por clase (acciones MSCI ACWI y bonos globales: "
  "50% AGG + 50% BNDX).")
TB(["2016–2026, en USD", "Retorno anual", "Volatilidad", "Sharpe", "Máx. caída"], [
    ["Nexum (comisión de 0,1%)", "9,9%", "10,6%", "0,74", "−20,5%"],
    ["Benchmark oficial (EE.UU.)", "10,5%", "11,5%", "0,75", "−22,8%"],
    ["Referencia global (ACWI + bonos globales)", "9,1%", "10,1%", "0,70", "−19,8%"]],
   nota="Subperíodos (benchmark EE.UU. vs referencia global): 2016–19 11,3% vs 8,7%; 2020–22 3,9% vs 2,7%; 2023–24 16,1% vs 13,6%; 2025–26 14,8% vs 16,8%.",
   anchos=[6, 2.5, 2.5, 2, 2.5])
P("El benchmark de EE.UU. es más exigente que el global (10,5% contra 9,1%), así que Nexum se mide contra la vara más alta. El tracking error se "
  "mide contra el benchmark del mismo universo: contra un índice global mezclaría las apuestas activas con la diferencia entre EE.UU. y el resto del "
  "mundo. Limitación: la cartera depende de una sola economía, y en 2025–2026 el mundo rindió más que EE.UU. (16,8% contra 14,8%). La diversificación "
  "internacional se evaluará en la revisión anual del IPS: en el backtest, pasar 5 puntos del S&P 500 a acciones de países desarrollados (EFA) no "
  "cambia la volatilidad y sube la probabilidad prudente de las tres metas en 0,7 puntos.")

H("4. Métricas de desempeño", 2)
P("Todas las métricas se calculan con retornos mensuales (anualizados con √12 para la volatilidad y ×12 para las medias), en CLP para la cartera y el "
  "benchmark. En el período en vivo, de pocas semanas, se usan retornos semanales y se informa el número de observaciones.")
TB(["Métrica", "Cálculo", "Para qué sirve", "Limitación"], [
    ["Retorno anual (CAGR)", "(valor final ÷ valor inicial)^(12/N) − 1", "Crecimiento compuesto comparable", "No dice nada del riesgo"],
    ["Volatilidad", "σ mensual × √12", "Riesgo total frente al límite de 10–12%", "Castiga igual las alzas y las caídas"],
    ["Máxima caída", "mín(V ÷ máximo previo − 1)", "Pérdida frente a la tolerancia de 25%", "Depende del período"],
    ["VaR y CVaR 95% mensual", "Percentil 5 de los retornos y promedio bajo él", "Riesgo de cola", "Pocas observaciones en la cola"],
    ["Sharpe", "(retorno − tasa libre de riesgo) ÷ volatilidad", "Retorno por unidad de riesgo total", "Supone retornos cercanos a la normal"],
    ["Treynor", "(retorno − tasa libre de riesgo) ÷ beta", "Retorno por unidad de riesgo de mercado", "Útil solo en carteras diversificadas"],
    ["Beta", "cov(cartera, S&P 500) ÷ var(S&P 500)", "Sensibilidad al mercado", "Cambia en el tiempo"],
    ["Alfa de Jensen", "Retorno sobre lo que predice el CAPM", "Valor agregado ajustado por beta", "Depende del índice de mercado elegido"],
    ["Tracking error ex-ante y ex-post", "σ(cartera − benchmark) × √12; ex-ante con la matriz de covarianzas y los pesos objetivo", "Riesgo activo frente al rango de 2–4%", "En períodos cortos es muy ruidoso"],
    ["Information ratio", "Retorno activo anual ÷ tracking error", "Calidad de la gestión activa", "Necesita varios años para ser significativo"],
    ["Probabilidad de cada meta", "Escenarios que la financian ÷ 20.000", "Vincula la cartera con los objetivos del cliente", "Depende de los supuestos del Montecarlo"]],
   nota="Tasa libre de riesgo: letras del Tesoro (BIL) para las métricas en USD; para las métricas en CLP, la tasa de los PDBC del Banco Central de Chile.",
   anchos=[3, 4.5, 4.5, 4])
PEND("Agregar la serie de la tasa en CLP (PDBC o TPM) para calcular Sharpe, Treynor y alfa en pesos.")

H("5. Tracking error objetivo", 2)
P(f"El tracking error objetivo sale de dividir el alfa que se busca por el information ratio que un gestor competente puede sostener: "
  f"TE = alfa ÷ IR = 1,5% ÷ 0,5 = 3%. El máximo usa un alfa de 2%: 2% ÷ 0,5 = 4% (Grinold y Kahn, 2000). El mínimo de 2% asegura que la "
  f"gestión sea realmente activa: con menos, la cartera sería casi una réplica del benchmark. En el backtest 2016–2026 el tracking error "
  f"frente al benchmark oficial es {p_(c_('2016-2026', 'USD 10', 'USD', 'Tracking error'))}, dentro del rango.")

H("6. Backtesting", 2)
P("Datos: precios diarios ajustados de Yahoo Finance (2009–2026) y la composición histórica del S&P 500. Los backtests de las estrategias corren "
  "desde 2013 y la cartera se evalúa en 2016–2026 (Momentum en acciones necesita la historia del ETF QMOM, disponible desde dic-2015).")
P("Controles de sesgo: sin anticipación (la señal se calcula al cierre del mes t y el retorno se mide desde t+1); sin supervivencia (el universo "
  "incluye las empresas que salieron del índice en cada fecha); sin sobreajuste (validación fuera de muestra: se calibra con 2013–2019 y se prueba "
  "con 2020–2026; además, 18 variantes de parámetros muestran que la regla vigente no es la mejor, lo que es evidencia en contra del sobreajuste).")
P("Costos de transacción: el modelo anterior descontaba 0,1% del monto transado. En StockTrak la comisión es fija, USD 10 por orden, así que pesa "
  "más en las estrategias chicas. El backtest se recalculó cobrando USD 10 por cada acción que entra o sale, sobre el capital de cada satélite "
  "(peso × USD 150.000).")
TB(["Estrategia (2016–2026, USD)", "Retorno con 0,1%", "Retorno con USD 10 por orden", "Órdenes por mes"],
   [[n, p_(e_(k, "0,1%")["CAGR"].iloc[0]), p_(e_(k, "USD 10/orden")["CAGR"].iloc[0]), n_(e_(k, "órdenes por mes (prom.)")["CAGR"].iloc[0], 1)]
    for k, n in [("MOM_EQ", "Momentum en acciones"), ("LOW_VOL", "Low-Volatility"), ("MOM_CMD", "Momentum en commodities")]], anchos=[5.5, 3.5, 4.5, 2.5])
P(f"Con la comisión fija, Momentum en acciones pierde casi todo su exceso de retorno: con USD 10.600 de capital y ~9 órdenes al mes, la comisión "
  f"equivale a cerca de 10% al año. Esto explica por qué en la gestión en vivo se redujo de 10 a 7 acciones, se fijó una orden mínima de USD 500 "
  f"y se usa una banda de permanencia (una acción se mantiene mientras siga en el top 25), que reduce la rotación. El backtest todavía no "
  f"incluye la banda de permanencia, así que sobrestima las órdenes.")
PEND("Rehacer el backtest de Momentum con 7 acciones y la banda de permanencia del top 25, y decidir con ese resultado si el satélite se mantiene, "
     "se agranda (con núcleo de 60%) o se reemplaza por el ETF QMOM, que no paga comisión por cada acción.")
TB(["2016–2026", "Nexum USD", "Benchmark USD", "Nexum CLP", "Benchmark CLP"], [
    ["Retorno anual", p_(c_("2016-2026", "USD 10", "USD", "CAGR Nexum")), p_(c_("2016-2026", "USD 10", "USD", "CAGR benchmark")), p_(c_("2016-2026", "USD 10", "CLP", "CAGR Nexum")), p_(c_("2016-2026", "USD 10", "CLP", "CAGR benchmark"))],
    ["Volatilidad", p_(c_("2016-2026", "USD 10", "USD", "Vol. Nexum")), p_(c_("2016-2026", "USD 10", "USD", "Vol. benchmark")), p_(c_("2016-2026", "USD 10", "CLP", "Vol. Nexum")), p_(c_("2016-2026", "USD 10", "CLP", "Vol. benchmark"))],
    ["Máx. caída", p_(c_("2016-2026", "USD 10", "USD", "Máx. caída Nexum")), p_(c_("2016-2026", "USD 10", "USD", "Máx. caída benchmark")), p_(c_("2016-2026", "USD 10", "CLP", "Máx. caída Nexum")), p_(c_("2016-2026", "USD 10", "CLP", "Máx. caída benchmark"))],
    ["Tracking error", p_(c_("2016-2026", "USD 10", "USD", "Tracking error")), "—", p_(c_("2016-2026", "USD 10", "CLP", "Tracking error")), "—"],
    ["Information ratio", n_(c_("2016-2026", "USD 10", "USD", "Information ratio"), 2), "—", n_(c_("2016-2026", "USD 10", "CLP", "Information ratio"), 2), "—"]],
   nota="Cartera con la comisión de USD 10 por orden; cartera y benchmark sin cobertura cambiaria. En CLP, retorno en USD más la variación del dólar observado.",
   anchos=[3.5, 3, 3, 3, 3])
P("Lectura: en pesos, la cartera rinde menos que el benchmark en una década excepcional para las acciones de EE.UU., pero con menos volatilidad y una "
  "caída máxima más baja. Su objetivo es financiar las metas con un riesgo moderado, no superar al índice en un mercado alcista. El information ratio "
  "negativo indica que, después de costos, la parte activa no agregó retorno en el backtest; ese es el punto que más se debe vigilar en vivo.")

H("7. Simulación de Montecarlo", 2)
P("Método: 20.000 escenarios de 50 años armados sorteando meses reales de 2013 a 2026 (bootstrap). En cada mes sorteado se toman juntos el retorno de la "
  "cartera y la variación del dólar, lo que conserva sus correlaciones. Hay dos versiones: la histórica usa los retornos tal como ocurrieron "
  f"({p_(g('Nexum', 'Hist', 'USD', 'Retorno real anual'))} real anual) y la prudente mantiene la volatilidad y las correlaciones pero recorta el retorno a "
  f"{p_(g('Nexum', 'Prosp', 'USD', 'Retorno real anual'))} real. Educación y Villarrica se evalúan en UF y la herencia en USD reales. Los pagos siguen el orden "
  f"de prioridad: Educación, luego Villarrica; la herencia es lo que queda en el año 50.")
cm = C["montecarlo"]; k_ = lambda esc, mon, col: cm[(cm.Escenario.str.startswith(esc)) & (cm["Moneda de las metas"] == mon)][col].iloc[0]
TB(["Probabilidad de financiar", "Histórico, en USD", "Histórico, metas en su moneda", "Prudente, en USD", "Prudente, metas en su moneda"], [
    [col.replace("P(", "").replace(")", "").replace("3 objetivos", "Las tres metas"), p_(k_("Hist", "USD", col)), p_(k_("Hist", "UF", col)),
     p_(k_("Prud", "USD", col)), p_(k_("Prud", "UF", col))]
    for col in ["P(Educación)", "P(Villarrica)", "P(Herencia)", "P(3 objetivos)"]],
   nota=f"Serie de la cartera con la comisión de USD 10 por orden. La cartera actual de la AGF, en el escenario prudente con las metas en su moneda, financia las tres metas en {p_(g('AGF 85/15', 'Prosp', 'UF', 'P(3 objetivos)'))}.",
   anchos=[4, 2.8, 3.2, 2.8, 3.2])
P("Medir en dólares sobrestima Villarrica en unos 7 puntos: esa es la diferencia que el comité llamó una ilusión óptica. La conclusión que se presenta a la "
  "familia usa la columna prudente con cada meta en su moneda: Educación está asegurada, y Villarrica y la herencia dependen de las palancas.")
TB(["Palanca (prudente, metas en su moneda)", "Educación", "Villarrica", "Herencia", "Las tres metas"],
   [[i, p_(r["P(Educación)"]), p_(r["P(Villarrica)"]), p_(r["P(Herencia)"]), p_(r["P(3 objetivos)"])] for i, r in pu.iterrows()], anchos=[6, 2.5, 2.5, 2.5, 2.5])
de = T["Desempleo"]; d_ = lambda i: de.iloc[i]
P(f"Desempleo de Tomás: si se modela que Tomás pierde el empleo con mayor probabilidad cuando la cartera cae, Educación se mantiene sobre 99%. Con pérdida "
  f"permanente del empleo, en el escenario prudente las tres metas bajan a {p_(d_(9)['P(3 objetivos)'])} y Educación queda en {p_(d_(9)['P(Educación)'])}. "
  f"Mitigantes: fondo de emergencia fuera del mandato, seguro de vida e invalidez y tecnología acotada a ~14% de la cartera.")
PEND("Correr el Montecarlo con la UF directamente (dólar en UF = dólar observado ÷ UF) en vez del dólar nominal sin tendencia, cuando esté disponible la serie histórica de la UF.")

H("8. Conclusión de la estrategia", 2)
P("La cartera propuesta es coherente con un perfil moderado: 62,5% en renta variable, volatilidad dentro del rango una vez cubierto el dólar y una caída "
  "histórica menor que la del benchmark y la de la AGF. Educación se financia en prácticamente todos los escenarios. Villarrica y la herencia no están "
  "aseguradas con supuestos prudentes, y lo decimos con transparencia: la familia tiene dos palancas concretas para subir esa probabilidad. "
  "El punto débil es la gestión activa después de costos; las decisiones pendientes de esta versión apuntan a corregirlo.")
doc.add_page_break()

# ================================================================== PARTE III · Resultados (borrador)
H("Parte III · Resultados de la gestión (borrador, completar al cierre del trading)", 1)
P("Las cifras siguientes llegan al 16-oct-2026 (cinco semanas) y están en USD. Deben actualizarse al cierre del trading y pasarse a CLP.")
TB(["Indicador (14-sep a 16-oct)", "Nexum", "Benchmark oficial", "Límite del IPS"], [
    ["Retorno acumulado", "−1,03%", "−0,01%", "—"], ["Volatilidad anualizada", "6,4%", "8,1%", "10–12%"], ["Beta vs S&P 500", "0,50", "0,74", "—"],
    ["Máxima caída", "−2,3%", "−2,3%", "25%"], ["Tracking error anualizado (5 observaciones semanales)", "3,2%", "—", "2–4%"],
    ["Semanas sobre el benchmark", "2 de 5", "—", "—"]], anchos=[7, 2.5, 3, 3])
P("Atribución por clase de activo: la brecha de −1,02 puntos se explica por renta variable (−0,52; Low-Volatility y las pérdidas de Dell y AMD en Momentum), "
  "commodities (−0,52; la entrada en petróleo frente al índice DJP) y renta fija (−0,02, replica su índice). Comisiones: 69 operaciones × USD 10 = USD 690 "
  "(0,46% del capital).")
PEND("Atribución de Brinson (asignación, selección e interacción) en CLP, con un efecto cambiario separado, de modo que los efectos sumen el retorno activo.")
PEND("Evolución semanal del tracking error frente al rango de 2% a 4%, con una sola definición (desviación estándar de los retornos activos semanales × √52).")
PEND("Ganancias y pérdidas por posición al cierre, conciliadas con StockTrak, incluyendo lo realizado y las comisiones.")
PEND("Conteo final de transacciones (mínimo 150) y bitácora de decisiones con fecha y motivo.")
PEND("Perspectivas 2027–2031: escenarios de tasas e inflación, efecto esperado sobre la probabilidad de cada meta, gatillos de revisión y palancas (rúbrica D1).")
doc.add_page_break()

H("Referencias", 1)
for ref in ["Ang, A., Hodrick, R., Xing, Y. y Zhang, X. (2006). The cross-section of volatility and expected returns. Journal of Finance, 61(1), 259–299.",
            "Black, F. y Litterman, R. (1992). Global portfolio optimization. Financial Analysts Journal, 48(5), 28–43.",
            "Bodie, Z., Kane, A. y Marcus, A. Investments. McGraw-Hill (capítulos de evaluación de desempeño y gestión activa de carteras).",
            "Brinson, G., Hood, L. y Beebower, G. (1986). Determinants of portfolio performance. Financial Analysts Journal, 42(4), 39–44.",
            "Campbell, J., Serfaty-de Medeiros, K. y Viceira, L. (2010). Global currency hedging. Journal of Finance, 65(1), 87–121.",
            "CFA Institute. Code of Ethics and Standards of Professional Conduct.",
            "Frazzini, A. y Pedersen, L. (2014). Betting against beta. Journal of Financial Economics, 111(1), 1–25.",
            "Grable, J. y Lytton, R. (1999). Financial risk tolerance revisited. Financial Services Review, 8, 163–181.",
            "Grinold, R. y Kahn, R. (2000). Active Portfolio Management. McGraw-Hill.",
            "He, G. y Litterman, R. (1999). The intuition behind Black-Litterman model portfolios. Goldman Sachs.",
            "Jegadeesh, N. y Titman, S. (1993). Returns to buying winners and selling losers. Journal of Finance, 48(1), 65–91.",
            "Ley N.° 19.913. Crea la Unidad de Análisis Financiero. Diario Oficial de Chile, 18-dic-2003.",
            "McLean, R. y Pontiff, J. (2016). Does academic research destroy stock return predictability? Journal of Finance, 71(1), 5–32.",
            "Moskowitz, T., Ooi, Y. y Pedersen, L. (2012). Time series momentum. Journal of Financial Economics, 104(2), 228–250."]:
    q = doc.add_paragraph(ref); q.paragraph_format.space_after = Pt(3)
PEND("Verificar cada referencia y agregar el material del profesor guía y los slides del profesor Castañeda.")

H("Anexo 1 · Cuestionario de tolerancia al riesgo (Grable y Lytton, 1999)", 1)
P("Respuestas simuladas por el equipo con apoyo de IA a partir de la información del caso. Puntaje total: 30 de un rango de 13 a 47.")
TB(["Pregunta (resumen)", "Respuesta", "Puntaje"], [
    ["Cómo te describiría un amigo como tomador de riesgo", "Dispuesto a tomar riesgos después de investigar", "3"],
    ["Programa de TV: qué elegirías", "50% de ganar USD 5.000", "2"],
    ["Pierdes el empleo antes de unas vacaciones", "Tomar unas vacaciones más modestas", "2"],
    ["Recibes USD 20.000 para invertir", "Acciones o fondos de acciones", "3"],
    ["Experiencia invirtiendo en acciones", "Algo cómodo", "2"],
    ["Palabra asociada a riesgo", "Oportunidad", "3"],
    ["Bonos del gobierno vs activos reales", "Vender la mitad y poner la mitad en activos reales", "2"],
    ["Mejor y peor caso de cuatro alternativas", "Ganar USD 2.600 o perder USD 800", "3"],
    ["Ganancia segura vs apuesta (USD 1.000)", "Ganancia segura de USD 500", "1"],
    ["Pérdida segura vs apuesta (USD 2.000)", "50% de perder USD 1.000", "3"],
    ["Herencia de USD 100.000 en un solo instrumento", "Fondo mixto de acciones y bonos", "2"],
    ["Distribución de USD 20.000", "30% bajo, 40% medio y 30% alto riesgo", "2"],
    ["Inversión en una mina de oro (20% de éxito)", "Un mes de sueldo", "2"]], anchos=[7, 7, 2])
P("Validación: el simulador de perfil de Banchile Inversiones entrega perfil moderado, con recomendación de hasta 60% en renta variable.")

os.makedirs(os.path.dirname(SALIDA), exist_ok=True); doc.save(SALIDA); print(SALIDA)
