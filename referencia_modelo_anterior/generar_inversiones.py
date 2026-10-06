# -*- coding: utf-8 -*-
"""Genera Inversiones.pdf: monto y stop-loss por posicion para partir en StockTrak.

Lee _inversiones_data.json (generado por _gen_inversiones_data.py, que corre
las mismas reglas de senal que Senales_Hoy.py y le agrega precio actual, ATR
y tamano de posicion). No recalcula nada del backtest -- es una capa de
ejecucion sobre la cartera recomendada (09b_Black_Litterman).
"""
import json
import os

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                 PageBreak, ListFlowable, ListItem, HRFlowable)
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Inversiones.pdf")
DATA_PATH = os.path.join(HERE, "_inversiones_data.json")

NAVY = colors.HexColor("#1F4E78")
NAVY_DARK = colors.HexColor("#17365D")
GREY = colors.HexColor("#595959")
LIGHTGREY = colors.HexColor("#E7E6E6")
BLUE_NOTE = colors.HexColor("#D9E1F2")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitlePage", fontSize=24, leading=30, textColor=NAVY_DARK, spaceAfter=6, fontName="Helvetica-Bold"))
styles.add(ParagraphStyle(name="SubtitlePage", fontSize=13, leading=18, textColor=GREY, spaceAfter=4))
styles.add(ParagraphStyle(name="H1", fontSize=15, leading=19, textColor=colors.white, backColor=NAVY,
                           spaceBefore=14, spaceAfter=10, leftIndent=6, borderPadding=(6, 6, 6, 6), fontName="Helvetica-Bold"))
styles.add(ParagraphStyle(name="H2", fontSize=12, leading=15, textColor=NAVY_DARK, spaceBefore=10, spaceAfter=6, fontName="Helvetica-Bold"))
styles.add(ParagraphStyle(name="Body", fontSize=9.5, leading=13.5, alignment=TA_JUSTIFY, spaceAfter=8))
styles.add(ParagraphStyle(name="BodySmall", fontSize=8.5, leading=12, alignment=TA_JUSTIFY, textColor=GREY, spaceAfter=6))
styles.add(ParagraphStyle(name="Note", fontSize=9, leading=13, alignment=TA_JUSTIFY, backColor=BLUE_NOTE,
                           borderPadding=(8, 8, 8, 8), spaceAfter=10))
styles.add(ParagraphStyle(name="BulletItem", fontSize=9.5, leading=13.5, alignment=TA_JUSTIFY, spaceAfter=4, leftIndent=10))


def h1(t): return Paragraph(t, styles["H1"])
def h2(t): return Paragraph(t, styles["H2"])
def body(t): return Paragraph(t, styles["Body"])
def small(t): return Paragraph(t, styles["BodySmall"])
def note(t): return Paragraph(t, styles["Note"])
def bullets(items):
    return ListFlowable([ListItem(Paragraph(it, styles["BulletItem"])) for it in items],
                         bulletType="bullet", start="•", leftIndent=14)


def table(data, col_widths=None, header=True, small_font=False):
    fs = 7.5 if small_font else 8.5
    t = Table(data, colWidths=col_widths, hAlign="LEFT")
    style = [
        ("FONTSIZE", (0, 0), (-1, -1), fs),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BFBFBF")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
    ]
    if header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), LIGHTGREY),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ]
    t.setStyle(TableStyle(style))
    return t


def usd(x):
    return f"${x:,.2f}"


def pct(x):
    return f"{100*x:.2f}%"


def position_table(rows, with_stop=True):
    headers = ["Ticker", "Precio", "Acciones", "Invertido", "Costo op.", "Sobrante"]
    if with_stop:
        headers.append("Stop-loss")
        headers.append("Riesgo/acción")
    data = [headers]
    for r in rows:
        row = [r["ticker"], usd(r["precio"]), str(r["acciones"]), usd(r["invertido"]),
               usd(10.0), usd(r["sobrante"])]
        if with_stop:
            sl = r.get("stop_loss")
            if sl:
                row.append(usd(sl))
                row.append(f"{pct((r['precio']-sl)/r['precio'])}")
            else:
                row.append("n/d")
                row.append("n/d")
        data.append(row)
    return data


def main():
    with open(DATA_PATH) as f:
        d = json.load(f)

    story = []

    # ---------------- PORTADA ----------------
    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph("MODELO NEXUM", styles["TitlePage"]))
    story.append(Paragraph("Órdenes de Inversión — Cartera Recomendada (Black-Litterman)", styles["SubtitlePage"]))
    story.append(Paragraph("Familia Cunich Allende", styles["SubtitlePage"]))
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", color=NAVY, thickness=1))
    story.append(Spacer(1, 0.5 * cm))
    story.append(body(
        f"Monto, número de acciones y stop-loss recomendado para partir invirtiendo en StockTrak con "
        f"USD {d['capital_invertible']:,.0f} (capital total menos el 4% de reservas — Fondo de Emergencia "
        f"y cobertura cambiaria). Precios y elegibilidad calculados con datos de mercado del "
        f"{d['fecha']} (no es el cache congelado de los backtests). Universo S&P 500: snapshot del "
        f"{d['snap_membership']}."
    ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(note(
        "<b>Costo de transacción:</b> USD 10 por posición (asumido según indicación del cliente). Se "
        "descuenta del capital asignado a cada posición ANTES de calcular cuántas acciones comprar — por "
        "eso el número de acciones a veces deja más efectivo \"sobrante\" del esperado (el sobrante es la "
        "suma del descuento por comisión más el resto por redondeo a acciones enteras; StockTrak no permite "
        "fracciones de acción)."
    ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(note(
        "<b>Stop-loss:</b> se calcula como precio actual − 2 × ATR(14) (Average True Range de 14 ruedas), "
        "un método estándar de trend-following que se adapta a la volatilidad real de cada activo — un "
        "stop más ajustado para acciones tranquilas (ej. Low-Volatility) y más amplio para las más volátiles "
        "(ej. Momentum). <b>Esto es una herramienta de gestión de riesgo para la ejecución real — no formó "
        "parte del backtest del modelo</b> (los backtests rebalancean mensualmente sin stop-loss "
        "intramensual); no cambia ningún resultado de Sharpe/CAGR reportado en Informe_Estrategia_Nexum_"
        "Final.pdf. Es una sugerencia de punto de salida, no una garantía de ejecución exacta a ese precio."
    ))
    story.append(PageBreak())

    # ---------------- RESUMEN ----------------
    story.append(h1("1. Resumen de Capital por Sleeve"))
    cap_total = d["capital_invertible"]
    story.append(table([
        ["Sleeve", "Peso BL", "Capital asignado"],
        ["SPY (núcleo pasivo)", pct(d["weights"]["SPY"]), usd(d["cap_spy"])],
        ["TLH (núcleo pasivo)", pct(d["weights"]["TLH"]), usd(d["cap_tlh"])],
        ["VCLT (núcleo pasivo)", pct(d["weights"]["VCLT"]), usd(d["cap_vclt"])],
        ["Commodities (satélite)", pct(d["weights"]["MOM_CMD"]), usd(d["cap_cmd"])],
        ["Momentum de acciones (satélite)", pct(d["weights"]["MOM_EQ"]), usd(d["cap_mom"])],
        ["Low-Volatility (satélite)", pct(d["weights"]["LOW_VOL"]), usd(d["cap_lv"])],
        ["Total", "100,00%", usd(cap_total)],
    ], col_widths=[6*cm, 3*cm, 5*cm]))
    story.append(Spacer(1, 8))
    story.append(body(
        "Cada sleeve recibe capital = peso Black-Litterman (09b_Black_Litterman!D62:D67) × "
        f"USD {cap_total:,.0f}. Dentro de Momentum y Low-Volatility, ese capital se reparte en partes "
        "iguales entre las 10 posiciones (equal-weight, igual que en el backtest). Dentro de Commodities, "
        "se reparte en partes iguales entre los instrumentos que tienen señal hoy (puede ser menos de 5)."
    ))
    story.append(PageBreak())

    # ---------------- NUCLEO PASIVO ----------------
    story.append(h1("2. Núcleo Pasivo — SPY / TLH / VCLT"))
    story.append(body(
        "Implementación directa (no rota, no tiene stop-loss — es la base estratégica de largo plazo del "
        "mandato, ver Informe_Estrategia_Nexum_Final.pdf sección 3)."
    ))
    story.append(table(position_table(d["core_rows"], with_stop=False), col_widths=[3*cm, 3*cm, 2.5*cm, 3*cm, 2.5*cm, 2*cm]))
    story.append(PageBreak())

    # ---------------- MOMENTUM ----------------
    story.append(h1(f"3. Momentum de Acciones — {len(d['rows_mom'])} posiciones"))
    story.append(body(
        f"Capital de sleeve: {usd(d['cap_mom'])} ({pct(d['weights']['MOM_EQ'])} del capital invertible), "
        f"repartido en {len(d['rows_mom'])} posiciones de {usd(d['cap_mom']/max(len(d['rows_mom']),1))} cada una."
    ))
    story.append(table(position_table(d["rows_mom"]), col_widths=[1.8*cm, 1.8*cm, 1.6*cm, 2.1*cm, 1.7*cm, 1.7*cm, 1.8*cm, 1.8*cm], small_font=True))
    story.append(Spacer(1, 6))
    story.append(small(
        "Rebalanceo mensual: correr Senales_Hoy.py (o _gen_inversiones_data.py) el mismo día de cada mes "
        "para actualizar la lista de 10 posiciones y sus stop-loss."
    ))
    story.append(PageBreak())

    # ---------------- LOW-VOL ----------------
    story.append(h1(f"4. Low-Volatility — {len(d['rows_lv'])} posiciones"))
    story.append(body(
        f"Capital de sleeve: {usd(d['cap_lv'])} ({pct(d['weights']['LOW_VOL'])} del capital invertible), "
        f"repartido en {len(d['rows_lv'])} posiciones de {usd(d['cap_lv']/max(len(d['rows_lv']),1))} cada una."
    ))
    story.append(table(position_table(d["rows_lv"]), col_widths=[1.8*cm, 1.8*cm, 1.6*cm, 2.1*cm, 1.7*cm, 1.7*cm, 1.8*cm, 1.8*cm], small_font=True))
    story.append(PageBreak())

    # ---------------- COMMODITIES ----------------
    story.append(h1(f"5. Commodities — {len(d['rows_cmd'])} de 5 posibles"))
    story.append(body(
        f"Capital de sleeve: {usd(d['cap_cmd'])} ({pct(d['weights']['MOM_CMD'])} del capital invertible). "
        f"Universo: GLD, USO, DBA, SLV, CPER — hoy pasan el filtro de señal {len(d['rows_cmd'])} de 5. "
        f"Si ninguno pasa, este tramo va 100% a BIL/SGOV hasta el próximo rebalanceo."
    ))
    if d["rows_cmd"]:
        story.append(table(position_table(d["rows_cmd"]), col_widths=[1.8*cm, 1.8*cm, 1.6*cm, 2.1*cm, 1.7*cm, 1.7*cm, 1.8*cm, 1.8*cm], small_font=True))
    else:
        story.append(note("Sin señal en ningún instrumento hoy — mantener este tramo en BIL/SGOV."))
    story.append(PageBreak())

    # ---------------- CIERRE ----------------
    story.append(h1("6. Notas Operativas"))
    story.append(bullets([
        "<b>Rebalanceo:</b> Momentum, Low-Volatility y Commodities rebalancean MENSUALMENTE — volver a "
        "correr el generador de este PDF el mismo día de cada mes. El núcleo pasivo no rota.",
        "<b>Costo de transacción:</b> se asumió USD 10 por posición tanto para la compra inicial como para "
        "cada rebalanceo futuro; confirmar la comisión real de StockTrak antes de operar y ajustar "
        "COSTO_TRANSACCION en _gen_inversiones_data.py si es distinta.",
        "<b>Stop-loss:</b> es una sugerencia de gestión de riesgo (2×ATR14), no una regla que el backtest "
        "del modelo haya probado — actívenlo como orden stop en StockTrak si la plataforma lo permite, o "
        "monitoreen manualmente el nivel.",
        "<b>Disponibilidad en StockTrak:</b> confirmar que todos los tickers de este documento estén "
        "disponibles en la plataforma antes de ingresar las órdenes (00_Inputs!D47).",
        "<b>Cumplimiento StockTrak:</b> recordar la limitación abierta documentada en "
        "Informe_Estrategia_Nexum_Final.pdf sección 10 — Momentum rebalancea mensual, no semanal, así que "
        "el volumen de transacciones exigido por la rúbrica (5+/semana) no se cumple solo con estas "
        "posiciones.",
    ]))

    doc = SimpleDocTemplate(OUT, pagesize=letter,
                             topMargin=2*cm, bottomMargin=2*cm, leftMargin=2*cm, rightMargin=2*cm,
                             title="Modelo Nexum - Órdenes de Inversión")
    doc.build(story)
    print("PDF generado:", OUT)


if __name__ == "__main__":
    main()
