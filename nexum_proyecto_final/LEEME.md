# Nexum — Proyecto final (versión auditada)

Grupo 11 · ESF 2026-2. Proyecto reconstruido desde cero a partir de la auditoría del modelo anterior
(`~/Desktop/Modelo_Final_Nexum`, que se conserva como referencia histórica).

## Entregables
| Archivo | Qué es |
|---|---|
| `informe/Informe_Final_Nexum.docx` | Informe IPS + Estrategia (base del informe final y de la defensa) |
| `modelo/Modelo_Nexum_v2.xlsx` | Modelo en Excel: fórmulas vivas (TIR, covarianzas, Black-Litterman), recalculado, 0 errores |
| `resultados/resultados_modelo.xlsx` | Todas las tablas de resultados |
| `informe/figuras/` | Gráficos del informe |

## Código (`codigo/`)
| Módulo | Contenido |
|---|---|
| `config.py` | Todos los parámetros (fuente única de verdad) |
| `datos.py` | Carga de datos (caché en `datos/`) |
| `estrategias.py` | Backtests point-in-time: Momentum, Low-Volatility, Momentum en commodities |
| `portafolio.py` | Markowitz, Black-Litterman, benchmark y métricas |
| `objetivos.py` | Flujos, TIR requerida, factibilidad, plan de desembolsos |
| `montecarlo.py` | Montecarlo en USD y UF, histórico y prospectivo |
| `validacion.py` | Robustez de parámetros y walk-forward |
| `analisis_complementario.py` | Contribución al riesgo, Montecarlo con desempleo de Tomás y abanico del patrimonio (rescatados del trabajo de Francisca y recalculados con el modelo oficial) |
| `run_all.py` | Corre todo y guarda `resultados/` (≈10 min; la robustez queda en caché) |
| `excel_modelo.py`, `figuras.py`, `informe.py` | Generan el Excel, los gráficos y el informe |
| `senales.py` | Señales de operación con precios del día (uso semanal/mensual) |
| `benchmark_djp.py` | Cambio de benchmark de commodities a DJP (Bloomberg Commodity Index TR, oct-2026): recalcula solo benchmark, métricas, tracking error y estrategias sobre los retornos oficiales, sin rehacer backtests. `run_all.py` ya usa DJP. Serie DJP agregada a `datos/extra_prices.parquet` desde `benchmark_style_prices.csv` del Drive del grupo |
| `analisis_adicional.py` | Benchmark por clase de activo, resultado en vivo por clase (exports de StockTrak del 6-oct en `datos/`), forward USD/CLP, bandas de rebalanceo, regla de commodities y activos adicionales → `resultados/analisis_adicional.xlsx` (correr después de `run_all.py`; `--desfase` agrega el control de calendario del backtest) |

Orden: `python3 run_all.py && python3 analisis_adicional.py && python3 excel_modelo.py && python3 figuras.py && python3 informe.py`.
El Excel debe abrirse y guardarse en Microsoft Excel una vez para que queden visibles los valores de las fórmulas.

## Correcciones respecto del modelo anterior
1. Se eliminaron los dos meses de 2018 que el modelo descartaba por un dato vacío de Low-Vol (162 → 164 meses).
2. El filtro de Sharpe de Momentum usa volatilidad de 12 meses (igual que en la operación real).
3. Black-Litterman calculado con fórmulas en el Excel (antes: columna π desplazada y valores pegados).
4. Benchmark único e invertible por sleeve (Low-Vol contra SPLV, Momentum contra QMOM; commodities contra DJP desde oct-2026).
5. Se eliminaron hojas y textos de la arquitectura anterior (calce LDI) y las referencias a Betting Against Beta.
6. Sesgo de selección del universo de commodities declarado y controlado.
La versión portada reproduce exactamente el modelo anterior antes de aplicar las correcciones (diferencia 10⁻¹⁶).
Los pesos aprobados se mantienen: recalibrados, difieren menos de 0,7 puntos.

## Pendiente para el grupo
- Aplicar el cuestionario de tolerancia al riesgo a los clientes (no simularlo).
- Actualizar la sección 5 del informe (implementación) con los resultados al cierre de la simulación.
- Convertir el informe en la presentación de 20 minutos.
