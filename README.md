# Simulación de Inversiones — Nexum (Grupo 11, ESF 2026-2)

## Versión oficial
**`nexum_proyecto_final/`** es la versión oficial del proyecto: coincide con lo que se opera en StockTrak
(pesos Black-Litterman aprobados, Momentum mensual de 10 acciones con regla 6m/12m, Low-Volatility y Momentum en commodities).

| Qué | Dónde |
|---|---|
| Informe IPS + Estrategia | `nexum_proyecto_final/informe/Informe_Final_Nexum.docx` |
| Modelo Excel (fórmulas vivas, 0 errores) | `nexum_proyecto_final/modelo/Modelo_Nexum_v2.xlsx` |
| Código (correr `codigo/run_all.py`) | `nexum_proyecto_final/codigo/` |
| Tablas de resultados | `nexum_proyecto_final/resultados/` |
| Detalle de la estructura y las correcciones | `nexum_proyecto_final/LEEME.md` |

## Otras carpetas
| Carpeta | Estado |
|---|---|
| `modelo_nexum/` | Trabajo previo de Francisca sobre NEXUM_FINAL_AUDITADO (incluía la "rotación semanal de 30 acciones", ya descartada). Se conserva como referencia |
| `stocktrak/` | Exportaciones de posiciones de StockTrak |
| `referencia_modelo_anterior/` | Scripts del modelo anterior: `_gen_inversiones_data.py` generó las órdenes iniciales del 14-sep (asume USD 10 de comisión por posición) |

## Reglas de trabajo
- `main` (cuando exista) contiene solo la versión oficial; cada uno trabaja en su rama y se integra con un pull request revisado por el otro.
- Las comisiones de StockTrak (~USD 10 por operación, ~USD 1.500 por las 150 operaciones exigidas) se tratan como costo operativo de la simulación: no entran en Black-Litterman ni en el Montecarlo.
- Las desviaciones discrecionales de la regla (p. ej. AFL/FRT el 21-sep, venta del petróleo el 2-oct) se documentan con fecha y motivo.
