# Análisis 17-nov (dudas de la defensa)

Corren sobre el modelo 12-nov de Matías (carpeta `codigo/` de *Modelo_12_Noviembre_Defensa*, con sus `datos/`), sin modificarlo.
Antes, generar `resultados/backtests_brutos.pkl` con `python3 m12_backtest.py` (~12 min).

| Script | Qué calcula |
|---|---|
| `a_tir_uf_y_moneda.py` | TIR requerida en UF; volatilidad y caídas de S&P 500, EFA y ACWI medidas en UF |
| `b_aversion_grable.py` | Cotas de la aversión al riesgo A a partir de las apuestas del cuestionario de Grable y Lytton |
| `c_defensa_calculos.py` | AGF con TAC; presupuesto de TE y TE óptimo; estrés 2022 y estrés inverso; táctica simple |
| `d_tactica_variantes.py` | Tres reglas de asignación táctica por tendencia de 10 meses |
| `informe_grupo.py` | Genera `entregables/Dudas_y_calculos_defensa_17nov.pdf` |

Uso: `python3 <script>.py RUTA/A/codigo_m12` (excepto b e informe_grupo, que no necesitan argumentos).
