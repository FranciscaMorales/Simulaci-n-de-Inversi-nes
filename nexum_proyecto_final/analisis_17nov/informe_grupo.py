"""Genera entregables/Dudas_y_calculos_defensa_17nov.pdf (resumen para el grupo)."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
F = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DV", F + "DejaVuSans.ttf")); pdfmetrics.registerFont(TTFont("DVB", F + "DejaVuSans-Bold.ttf"))
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "entregables", "Dudas_y_calculos_defensa_17nov.pdf")
b = ParagraphStyle("b", fontName="DV", fontSize=8.6, leading=11.2, spaceAfter=3)
h = ParagraphStyle("h", fontName="DVB", fontSize=10.5, leading=13, spaceBefore=6, spaceAfter=3, textColor=colors.HexColor("#1F3A5F"))
t = ParagraphStyle("t", fontName="DVB", fontSize=14, leading=17, spaceAfter=2)
s = ParagraphStyle("s", parent=b, textColor=colors.HexColor("#555555"))
E = []
P = lambda x, st=b: E.append(Paragraph(x, st))
def T(rows, w):
    tb = Table([[Paragraph(str(c), b) for c in r] for r in rows], colWidths=[x * cm for x in w])
    tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF5")), ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#BBBBBB")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)]))
    E.append(tb); E.append(Spacer(1, 4))
P("Nexum · Dudas y cálculos para la defensa (17-nov)", t)
P("Cálculos sobre el modelo 12-nov de Matías (sin modificarlo). Código: nexum_proyecto_final/analisis_17nov/. Montecarlo prospectivo, metas en su moneda, con comisión.", s)

P("Preguntas de Fran", h)
for q in ["1. Si la probabilidad conjunta es baja (35%), ¿por qué el cliente preferiría Nexum a su AGF?",
          "2. ¿Llevar el núcleo a 60% hace la estrategia más activa?", "3. ¿Cómo se valoriza la visión de mercado en Black-Litterman?",
          "4. ¿Cómo justificar invertir solo en EE.UU. (benchmark)? ¿Sirven la clasificación de riesgo, el riesgo cambiario y la menor variabilidad de EE.UU.?",
          "5. ¿La TIR de 4,65% usa bonos del Tesoro de EE.UU. o del Banco Central en UF?",
          "6. ¿Qué supuestos de estrés hacen creíble el Montecarlo?", "7. ¿Cuál es la aversión al riesgo del cliente (Grable-Lytton) y alcanza el TE?",
          "8. ¿Qué significa realmente una estrategia activa? ¿Basta con operar semana a semana evitando algunas operaciones por contexto?",
          "9. ¿El retorno de la AGF incluye su comisión? ¿Qué cobran los fondos balanceados en Chile? ¿Qué es la TAC?"]: P(q)

P("1 y 9 · AGF con su comisión (el profesor pide incluirla)", h)
P("El modelo simulaba la AGF sin comisión (37,2%). TAC = Tasa Anual de Costos: lo que el fondo cobra al año como % del patrimonio (CMF). "
  "Balanceados en Chile: mediana ~1,1–1,5%, promedio ~1,3–1,6% (AAFM, ago-2025); la CMF reportó ~2,1% en años anteriores.")
T([["Cartera", "P(3 metas)", "P(Villarrica)"], ["Nexum sin comisiones", "44,1%", "63,2%"], ["Benchmark pasivo (ETF)", "41,1%", "61,6%"],
   ["Nexum con USD 10 por orden", "35,1%", "57,1%"], ["AGF, TAC 1,09%", "19,8%", "42,4%"], ["AGF, TAC 1,47%", "15,0%", "37,7%"],
   ["AGF, TAC 1,61%", "13,5%", "36,2%"], ["AGF, TAC 2,10%", "8,8%", "30,8%"]], [7, 3, 3])
P("Lectura: frente a la AGF real, Nexum casi duplica la probabilidad. El competidor real es el pasivo barato (41%); la brecha es la comisión fija de StockTrak. Antes de costos, Nexum le gana (44%).")

P("2 y 8 · ¿Qué hace activa a la estrategia? Prueba de asignación táctica", h)
P("Activo = desviarse del benchmark con un proceso (visión → posición → control de riesgo → evaluación). La cantidad de órdenes no mide actividad "
  "(Cremers y Petajisto, 2009); más decisiones solo suben el IR si tienen habilidad (IR ≈ IC·√N, Grinold). Pasar el núcleo a 60% sube el TE (2,69%→3,43%) "
  "pero sigue siendo estático. Falta lo que pide el caso: apuestas por clase de activo y contexto. Se probó una regla de tendencia de 10 meses "
  "(Faber, 2007; Moskowitz, Ooi y Pedersen, 2012), señal del mes anterior, 2013–2026, con comisión:")
T([["Regla", "Retorno", "Máx. caída", "TE", "2022", "Órdenes/año extra"], ["Vigente", "8,91%", "−21,1%", "2,69%", "−16,2%", "0"],
   ["A: acciones↔bonos ±10%", "9,38%", "−21,8%", "2,77%", "−17,9%", "5"], ["B: acciones→caja si tendencia negativa (−10%)", "8,38%", "−20,3%", "3,16%", "−16,4%", "4"],
   ["C: cada clase a caja si su tendencia es negativa (−10% c/u)", "8,29%", "−18,0%", "3,45%", "−14,1%", "11"]], [5.9, 1.7, 1.9, 1.6, 2.0, 2.4])
P("C protege mejor (caída −18% y 2022 −14%) a cambio de −0,6 pp de retorno; A rinde más pero no protege. Decisión del grupo.")

P("3 · Black-Litterman", h)
P("Vistas actuales: S&P 500 rinde 6% (Q=0,06) y Low-Vol supera a commodities en 2 pp (Q=0,02); confianza Ω = diag(PτΣPᵀ), δ=2,5, τ=0,05. "
  "Falta: fuente de cada Q (CMA o prima del factor), aclarar si el 6% es total o en exceso, confianza explícita (Idzorek, 2005) y por qué no hay vista sobre Momentum.")

P("4 · Benchmark y EE.UU. (datos en UF, 2013–2026)", h)
T([["Activo", "Vol. en UF", "Peor caída en UF", "Corr. con USD/CLP"], ["S&P 500", "15,4%", "−29,0%", "−0,36"], ["Desarrollados sin EE.UU. (EFA)", "13,9%", "−25,5%", "−0,48"],
   ["Mundo (ACWI)", "14,1%", "−29,3%", "−0,45"]], [6, 3, 3.5, 3.5])
P("Ojo: en UF, invertir fuera de EE.UU. no fue más riesgoso (el peso chileno domina el riesgo y amortigua las caídas), y EFA sí diversifica (R² con SPY 0,68). "
  "No usar \"EE.UU. rindió mejor\" (en 2025–26 el mundo ganó) ni la clasificación soberana como argumento principal (EE.UU. es AA+/Aa1 y aplica a bonos, no a acciones). "
  "Argumentos defendibles: el benchmark sigue al universo invertido (SAMURAI, Bailey et al., 1990); la cobertura disponible y líquida en Chile es USD/CLP; "
  "ACWI ≈ S&P 500 (corr. 0,97). Reconocer la concentración como limitación revisable.")

P("5 · TIR", h)
P("La TIR no sale de un bono: es la tasa que iguala los flujos propios del cliente. En UF es la misma 4,65% (si el dólar real es estable); 4,47–4,96% si el dólar pierde o gana 1% real al año. "
  "Se compara con la tasa libre de riesgo en UF: swap cámara UF a 10 años ≈ 2,5–2,7% (BCCh, sep–oct 2026). Prima requerida ≈ 2 pp.")

P("6 · Estrés del Montecarlo", h)
P("Ya incluidos: remuestreo histórico y prospectivo (CMA), bloques de 12/24 meses, retorno ±1 pp, volatilidad cambiaria, dólar ±1% real, arancel, aportes nominales, desempleo, costo de cobertura. Nuevos:")
T([["Escenario", "Educación", "Villarrica", "3 metas"], ["Base", "99,7%", "57,1%", "35,1%"], ["Año tipo 2022 (−19% real) en el año 1", "98,8%", "38,2%", "18,2%"],
   ["2022 en el año 13 (antes de Educación)", "98,3%", "32,4%", "13,7%"], ["2022 en los años 1 y 13", "94,5%", "16,2%", "4,8%"],
   ["Estrés inverso: retorno real −3 pp/año", "97,8%", "20,4%", "1,4%"]], [7, 2.5, 2.5, 2.5])
P("Para llegar a 50% en las 3 metas hacen falta +0,7 pp de retorno real. Educación resiste todo. Literatura: Pfau y Young (sensibilidad a los supuestos: usar rangos de CMA), Kitces (a largo plazo el Montecarlo tiende a exagerar la volatilidad), Finke, Pfau y Blanchett (2013, riesgo de secuencia).")

P("7 · Aversión al riesgo y tracking error", h)
P("De las apuestas de Grable-Lytton (P2 y P8, utilidad CARA, riqueza USD 150.000): A ≥ 9. P9 es consistente con cualquier A > 0; P10 (arriesgar en pérdidas) no la explica ninguna A > 0: efecto de encuadre (Kahneman y Tversky, 1979). "
  "A implícita de la cartera (histórica): 7,7. Advertencia: apuestas chicas exageran A (Rabin, 2000); falta confirmar con el PDF del profesor. "
  "TE óptimo (U = E − ½Aσ², Grinold y Kahn): TE* = IR/A. Con A = 9: IR 0,2 → 2,2%; IR 0,35 → 3,9%; IR 0,5 → 5,6%. "
  "Presupuesto: respetando vol. ≤ 12% y caída ≥ −25%, el TE podría llegar a ~10,7% (corr. activo–benchmark −0,43). "
  "Conclusión: el TE actual (2,7%) usa poco del riesgo que el cliente permite; la banda 3–6% propuesta por Matías queda justificada ex ante por A.")

P("Decisiones pendientes", h)
for x in ["Elegir regla táctica (A, C o ninguna) y escribirla en el IPS.", "Adoptar banda de TE 3–6% justificada con A.", "Informe: AGF con TAC; reformular el argumento del benchmark; agregar estrés 2022 e inverso.",
          "Fran: enviar el PDF de Grable-Lytton para confirmar cómo el profesor calcula A.", "Faltan 43 operaciones antes del 4-dic."]: P("• " + x)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
SimpleDocTemplate(OUT, pagesize=A4, leftMargin=1.6 * cm, rightMargin=1.6 * cm, topMargin=1.3 * cm, bottomMargin=1.3 * cm).build(E); print(os.path.abspath(OUT))
