"""Nexum - parámetros del proyecto en un solo lugar (fuente única de verdad).

Todo parámetro que aparece en el Excel o el informe sale de aquí.
"""
import os

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATOS = os.path.join(BASE, "datos")
RESULTADOS = os.path.join(BASE, "resultados")
MODELO = os.path.join(BASE, "modelo")

# ---------------- Ventanas ----------------
FIN_DATOS = "2026-08-31"          # último mes completo usado para calibrar el modelo
INICIO_EVAL = "2013-01-31"        # ventana común de evaluación (162 meses)
INICIO_BENCH = "2016-01-31"       # QMOM existe desde dic-2015

# ---------------- Reglas comunes ----------------
COSTO_POR_LADO = 0.001            # 0,1% sobre el monto transado
# Convención del modelo aprobado: costo = 0,5 x suma|Δw| x 0,1% (cuenta un solo lado).
# Se reporta además la sensibilidad con ambos lados (validacion.py).
CONVENCION_COSTO_UN_LADO = True

# ---------------- Momentum en acciones ----------------
MOM = dict(top_n=10, max_sector=0.25, th_r3=0.00, th_r6=0.05, th_r12=0.10, sharpe_min=0.5,
           adv_min=5_000_000, inicio="2010-01-01",
           vol_sharpe="12m")   # "12m" = documentado y usado en la operación real; "1m" = versión original del backtest (error)

# ---------------- Low-Volatility ----------------
LV = dict(top_n=10, max_sector=0.25, precio_min=5.0, adv_min=5_000_000, inicio="2011-01-01")

# ---------------- Momentum en commodities ----------------
CMD = dict(universo=["GLD", "USO", "DBA", "SLV", "CPER"], universo_original=["GLD", "USO", "DBA"],
           th_r3=0.05, th_r6=0.08, th_r12=0.10, vol_max=0.50, inicio="2010-01-01")

# ---------------- Asignación estratégica ----------------
ACTIVOS = ["SPY", "TLH", "VCLT", "MOM_CMD", "MOM_EQ", "LOW_VOL"]
NOMBRES = {"SPY": "S&P 500 (SPY)", "TLH": "Tesoro EE.UU. 10-20 años (TLH)", "VCLT": "Corporativos largo plazo (VCLT)",
           "MOM_CMD": "Momentum en commodities", "MOM_EQ": "Momentum en acciones", "LOW_VOL": "Low-Volatility"}
NUCLEO_MIN, NUCLEO_MAX = 0.60, 0.70   # núcleo pasivo SPY+TLH+VCLT
PISO_BONOS = 0.08                     # piso TLH y VCLT (solo Markowitz)
BL_DELTA, BL_TAU = 2.5, 0.05
BL_VISTAS = [("Absoluta", {"SPY": 1.0}, 0.06, "Prima por riesgo accionaria de largo plazo"),
             ("Relativa", {"LOW_VOL": 1.0, "MOM_CMD": -1.0}, 0.02, "Low-Vol supera a commodities en 2 pp")]
# Pesos aprobados y en implementación desde sep-2026 (09b_Black_Litterman del modelo original)
PESOS_APROBADOS = {"SPY": 0.3789, "TLH": 0.1687, "VCLT": 0.1460, "MOM_CMD": 0.0611, "MOM_EQ": 0.0706, "LOW_VOL": 0.1746}

# ---------------- Benchmark de política (índices invertibles por sleeve) ----------------
BENCH = {"SPY": "SPY", "TLH": "TLH", "VCLT": "VCLT", "MOM_EQ": "QMOM", "LOW_VOL": "SPLV", "MOM_CMD": "DJP"}   # commodities: Bloomberg Commodity Index TR (DJP); antes, mezcla de los 5 ETF
TE_OBJETIVO, TE_MAX, IR_OBJETIVO, ALFA_OBJETIVO = 0.03, 0.04, 0.5, 0.015

# ---------------- Cliente y objetivos (enunciado) ----------------
USD_CLP, UF_CLP = 911.77, 40846.0     # BCCh, 11-ago-2026
CAPITAL = 150_000.0
RESERVA = 0.04                        # 2% caja operativa + 2% reserva cambiaria
APORTE, N_APORTES, MES_APORTE = 10_000.0, 19, 4
ARANCEL_CLP, ANOS_CARRERA = 65_000_000.0, 5
INICIO_VICENTE, INICIO_EMILIA = 14, 16
VILLARRICA_UF, ANO_VILLARRICA = 10_500.0, 25
HERENCIA_USD, ANO_HERENCIA = 500_000.0, 50
INFLACION_USD = 0.02

# ---------------- Montecarlo ----------------
N_SIMS, SEMILLA = 20_000, 777
# Supuestos prospectivos (reales, anuales). Construcción por bloques; ver informe sección 7.
CMA = {"SPY": 0.050, "TLH": 0.026, "VCLT": 0.032, "MOM_CMD": 0.020, "MOM_EQ": 0.055, "LOW_VOL": 0.045,
       "EFA": 0.055, "BONOS_GLOBAL": 0.020}
# Cartera actual de la AGF (enunciado): 85% (90% S&P 500 + 10% MSCI EAFE) + 15% Bloomberg Global Aggregate
AGF = {"SPY": 0.765, "EFA": 0.085, "BONOS_GLOBAL": 0.15}
