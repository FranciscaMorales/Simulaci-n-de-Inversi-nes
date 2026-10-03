# Auditoría Final — Modelo Nexum (`NEXUM_FINAL_AUDITADO`)

## A. Errores encontrados

1. **Desfase temporal en los 3 backtests** (Low-Volatility, Commodities, Rotación Semanal): la señal
   calculada en `t` se aplicaba al retorno de `(t+1, t+2]` en vez de `(t, t+1]`. Verificado leyendo
   el código y con trazas de fechas explícitas.
2. **Manejo incorrecto de NaN**: `serie.get(x, 0) or 0` no trata `NaN` como 0 en Python. Confirmados
   2 NaN en Low-Vol y 1 en Rotación, exactamente como se sospechaba.
3. **Ambigüedad en el tratamiento de reservas**: `00_Inputs!D46` dice "Fondo de emergencia dentro del
   mandato: No", lo que en una primera lectura llevó a esta auditoría a DEJAR de descontar esa reserva
   del capital de USD 150.000. El cliente aclaró posteriormente que ambas reservas (2% Money Market +
   2% cobertura cambiaria = 4% fijo) SÍ están incluidas dentro del 100% de la cartera calculada — la
   celda D46 se refiere a otra cosa (posiblemente si la reserva participa del trading activo del
   mandato, no si cuenta en la asignación total). Corregido con la aclaración del cliente como fuente.
4. **Benchmarks incorrectos**: Low-Volatility y Rotación Semanal se comparaban contra SPY llamándolo
   "proxy" de índices que SPY no replica (S&P Low Vol Index, S&P Momentum Index).
5. **Terminología incorrecta**: "Risk Parity"/"Equal Risk Contribution" para un prior que en realidad
   es Inverse-Volatility; "alfa" para un retorno activo que no es un intercepto de regresión.
6. **Afirmación falsa**: el informe decía que existía un "límite explícito de exposición a
   Tecnología" — no existe en ninguna hoja del Excel.
7. **Comparaciones no reproducibles**: RSP/VT/ACWI se citaban sin código ni datos que las
   respaldaran; al reproducirlas, la correlación de RSP con SPY resultó ser 0,939, no 0,96-0,97
   como se afirmaba.
8. **Atribución de fuente no verificable**: "6,5% real, Damodaran/Siegel" presentado como si fuera
   una cifra publicada específicamente para este caso.
9. **Ajuste del escenario de estrés hecho con shift aditivo** en vez de un factor geométrico
   multiplicativo sobre retornos brutos.
10. **Optimización circular potencial**: el diseño anterior usaba un "dial" de riesgo que se ajustaba
    hasta que Educación cumpliera un piso de probabilidad — riesgo de terminar optimizando pesos
    para lograr un número, no evaluando la cartera tal cual resulta del proceso Markowitz/BL/Solver.
11. **Monte Carlo con IID mensual como único método**, sin bootstrap de bloques ni verificación de
    convergencia entre 50.000 y 100.000 simulaciones.
12. **Sin modelar el riesgo cambiario/UF** de forma explícita ni como sensibilidad, pese a que
    Educación está en CLP y Villarrica en UF.

## B. Correcciones realizadas

- Reescritos los 3 backtests (`Backtesting_LowVolatility.py`, `Backtesting_Commodities.py`,
  `Backtesting_RotacionSemanal.py`) con el desfase corregido y manejo explícito de NaN, con
  validación automática de fechas impresa en cada corrida.
- Generado `PIT_COBERTURA.csv` con cobertura point-in-time por fecha (866 tickers históricos, 661
  con precio disponible, cobertura promedio 81,4%).
- Creado `BENCHMARKS_DEFINITIVOS.md` con benchmark real por estrategia: SPLV (S&P 500 Low
  Volatility Index) para Low-Vol, DJP (Bloomberg Commodity Index TR) para Commodities, SPY como
  benchmark amplio (no estilístico, explícitamente rotulado así) para Rotación Semanal.
- Reescrita la terminología: "Inverse-Volatility Reference Portfolio" en vez de "Risk Parity"; se
  verificó explícitamente que las risk contributions NO son iguales entre activos (8,42%-20,72%),
  confirmando que no es Equal Risk Contribution. "Retorno activo" en vez de "alfa" en código, Excel
  e informe.
- Creado `BlackLitterman_Nexum.py`, 100% reproducible, que persiste cada paso intermedio
  (`BL_inputs.csv`, `BL_prior.csv`, `BL_posterior.csv`, `BL_pesos.csv`). Las vistas quedan
  documentadas explícitamente como supuestos del equipo, no hechos garantizados.
- Recalculado Markowitz sobre los datos corregidos (mantenido como comparación, no como cartera
  final).
- Resuelto el tratamiento de reservas con la aclaración del cliente: Money Market (2%) + cobertura
  cambiaria (2%) = 4% fijo, INCLUIDAS dentro del 100% de la cartera total. Capital invertido en el
  motor de crecimiento: USD 144.000 (96% de USD 150.000) — un único escenario, no dos.
- Reconstruido el Monte Carlo (`Simulacion_Montecarlo.py`) sin ningún dial de ajuste de pesos:
  Moving Block Bootstrap (bloques de 12 meses como caso base; sensibilidad IID, 6 y 24 meses),
  50.000 simulaciones base + verificación de convergencia con 100.000, escenario prudente con
  ajuste geométrico multiplicativo, 7 stress tests adicionales, y sensibilidad de ventana completa.
- Reconstruido `Backtesting_BenchmarkCompuesto.py` con los pesos finales y los benchmarks reales.
- Eliminada la afirmación falsa sobre límite de exposición a Tecnología (no existe en el modelo).
- Reproducida la comparación RSP/VT/ACWI con datos reales descargados (ver `RSP_VT_ACWI_comparacion.csv`)
  y corregida la cifra de correlación de RSP.
- Creado `validar_modelo_final.py` con 12 comprobaciones automáticas.

## C. Metodología final

Cartera única de 6 activos (núcleo pasivo SPY+TLH+VCLT + satélite activo Commodities+Rotación
Semanal+Low-Volatility) financia los tres objetivos (Educación, Villarrica, Herencia) desde el
mismo pool, con pagos secuenciales por prioridad. Pesos optimizados vía Black-Litterman (prior
Inverse-Volatility + 2 vistas del equipo) con Solver de máximo Sharpe, restricción de núcleo pasivo
60-70%. Sin restricciones de piso individuales en BL (a diferencia de Markowitz, que sí las
necesita). Viabilidad evaluada con Monte Carlo de Moving Block Bootstrap, sin optimización
posterior de pesos contra la probabilidad resultante.

## D. Pesos definitivos

| Activo | Markowitz histórico | Black-Litterman (recomendado) |
|---|---|---|
| SPY | 51,77% | 37,40% |
| TLH | 8,00% (piso) | 15,89% |
| VCLT | 8,00% (piso) | 13,80% |
| Commodities | 7,52% | 11,65% |
| Rotación Semanal | 5,00% (piso) | 8,54% |
| Low-Volatility | 19,72% | 12,73% |
| Núcleo pasivo | 67,77% | 67,08% |
| Sharpe | 1,0399 | 0,3190 |

## E. Resultados definitivos de backtesting (corregidos)

| Estrategia | CAGR | Vol. anual | Sharpe | Max Drawdown |
|---|---|---|---|---|
| Low-Volatility | 11,24% | 11,84% | 0,963 | -18,60% |
| Commodities | 1,55% | 12,49% | 0,187 | -31,18% |
| Rotación Semanal | 10,88%* | 18,44% | 0,590 | -36,84% |

*Retorno anual promedio (52 semanas), no CAGR compuesto — la estrategia opera semanalmente.
Rotación Semanal cumple la rúbrica de StockTrak: 0 de 712 semanas bajo el mínimo de 5 operaciones,
248 operaciones en las últimas 12 semanas (objetivo 150-300).

## F. Resultados Black-Litterman

Ver `BL_prior.csv`, `BL_posterior.csv`, `BL_pesos.csv`. Inverse-Volatility Reference Portfolio,
δ=2,5, τ=0,05 (supuestos del equipo, documentados). Retorno posterior μ_BL entre 0,99% (Commodities)
y 4,25% (Rotación Semanal). Sharpe final 0,3190.

## G. Resultados Solver

**Confirmado con el Solver nativo de Excel en ambas hojas — RESUELTO, ya no es pendiente.**

- **Markowitz**: coincide exactamente con scipy en la primera corrida (Sharpe 1,0399).
- **Black-Litterman**: la primera corrida del Solver (Sharpe reportado 0,3224) no coincidía con scipy.
  Investigado: `09b_Black_Litterman!E51:E56` (μ_BL) se pega como valor fijo desde un cálculo en Python
  (decisión de diseño documentada en la propia hoja, para evitar encadenar MINVERSE/MMULT), y ese
  pegado había quedado desactualizado desde antes de esta auditoría — el prior y π sí estaban en vivo y
  coincidían exactamente con Python, pero μ_BL no. Corregido: repegado μ_BL desde `BL_posterior.csv`
  (recalculado con los datos auditados). Segunda corrida del Solver tras la corrección: **Sharpe
  0,318980727431369, pesos idénticos a scipy hasta el 7º decimal** (diferencia ~1e-7, ruido numérico).
  Ver `BL_pesos.csv` para los pesos finales usados en Monte Carlo y benchmark compuesto.

## H. Benchmark compuesto (pesos y benchmarks finales)

| Métrica | Valor |
|---|---|
| CAGR cartera | 8,82% |
| CAGR benchmark | 9,01% |
| Vol. cartera | 9,38% |
| Vol. benchmark | 9,87% |
| Retorno activo anual | -0,22% |
| Tracking Error | 2,29% |
| Information Ratio | -0,098 |

## I. Monte Carlo

Capital invertido: USD 144.000 (96% de USD 150.000; 4% en reservas fijas — Money Market 2% +
cobertura cambiaria 2% — incluidas dentro de la cartera total, confirmado por el cliente).

| Escenario | P(Educación) | P(Villarrica) | P(Herencia) | P(CONJUNTA) |
|---|---|---|---|---|
| Base (bloques 12 meses, 50.000 sims) | 100,0% | 96,40% | 90,00% | **90,00%** |
| IID mensual | 100,0% | 94,79% | 87,87% | 87,87% |
| Bloques 6 meses | 100,0% | 96,68% | 90,57% | 90,57% |
| Bloques 24 meses | 100,0% | 95,69% | 85,89% | 85,89% |
| Convergencia 100.000 sims | 100,0% | — | — | 90,05% (diff 0,05pp vs. 50.000) |
| Escenario prudente (6,5% geométrico) | 100,0% | 95,50% | 87,55% | 87,55% |

**Piso de Educación (>= 95%): CUMPLE en todos los escenarios probados (100,0%).**

Nota honesta: la probabilidad conjunta final (90,00%, verificada en 90,05% con 100.000 simulaciones)
es **menor** que el número reportado antes de esta auditoría (93,42%). La diferencia viene de
corregir los bugs reales de los backtests (que inflaban artificialmente el retorno de Commodities),
de usar bootstrap de bloques en vez de IID (reduce la probabilidad al preservar la autocorrelación
de las caídas de mercado), y de la reserva fija de 4% (no 2%) tras la aclaración del cliente. Se
acepta este número como el correcto.

## J. Stress tests

| Escenario | P(Educación) | P(Conjunta) |
|---|---|---|
| Base | 100,0% | 90,00% |
| Aportes terminan en año 10 | 100,0% | 76,19% |
| Shock inicial de mercado -30% | 100,0% | 75,34% |
| Inflación 4% (no 2%) | 100,0% | 41,08% |
| USD/CLP se deprecia 20% | 100,0% | 86,72% |
| UF se aprecia 15% | — | 84,25% |
| Retorno esperado -1pp | 100,0% | 71,77% |
| Retorno esperado +1pp | 100,0% | 97,25% |

Educación se mantiene en 100% en todos los stress tests — es robusta al tamaño del capital
agrupado, no a la suerte del período. La conjunta es sensible sobre todo a inflación alta y a
interrupción de aportes.

## K. Limitaciones

- No se dispone de las series oficiales de los índices institucionales (ICE US Treasury 10-20Y,
  Bloomberg US Corporate 10+Y) — TLH y VCLT son ellos mismos los ETF que replican esos índices, por
  lo que no hace falta proxy; pero SPLV y DJP sí son proxies (ETF/ETN) de sus índices, no las series
  oficiales del índice en sí.
- No se modela FX/UF estocásticamente a 50 años (se usa sensibilidad determinista, no un modelo de
  tipo de cambio de largo plazo).
- El margen de cobertura cambiaria (2%) queda como supuesto pendiente — no hay un flag explícito en
  `00_Inputs` que confirme si es parte del mandato o no.
- La cobertura point-in-time (81,4% promedio) reduce sustancialmente el survivorship bias, pero no
  lo elimina — persisten 205 tickers históricos sin precio disponible en la fuente de datos usada.
- ~~El Solver de Excel real no se ejecutó~~ — RESUELTO: corrido por el cliente en ambas hojas (ver
  sección G), confirma exactamente los resultados de scipy.optimize.

## L. Archivos modificados o creados

`Backtesting_LowVolatility.py`, `Backtesting_Commodities.py`, `Backtesting_RotacionSemanal.py`,
`Backtesting_BenchmarkCompuesto.py`, `Simulacion_Montecarlo.py`, `BlackLitterman_Nexum.py` (nuevo),
`validar_modelo_final.py` (nuevo), `Modelo_Nexum_Final_AUDITADO.xlsx`, `common_window_final.csv`,
`lowvol_monthly_returns.csv`, `mom_cmd_monthly_returns.csv`, `rotacion_semanal_returns.csv`,
`PIT_COBERTURA.csv` (nuevo), `BENCHMARKS_DEFINITIVOS.md` (nuevo), `BL_inputs.csv`, `BL_prior.csv`,
`BL_posterior.csv`, `BL_pesos.csv`, `Markowitz_pesos.csv`, `MC_resultados_principales.csv`,
`MC_sensibilidad_ventana.csv`, `MC_stress_tests.csv`, `MC_pesos_usados.csv`,
`BenchmarkCompuesto_resultados.csv`, `benchmark_style_prices.csv`, `RSP_VT_ACWI_comparacion.csv`,
`00_AUDITORIA_INICIAL.md` (nuevo), `AUDITORIA_FINAL_NEXUM.md` (nuevo, este documento).

## M. Supuestos pendientes (no inferibles del proyecto con certeza)

1. ~~Margen de cobertura cambiaria (2%): dentro o fuera del mandato~~ — RESUELTO por el cliente:
   ambas reservas (2%+2%=4%) están incluidas dentro del 100% de la cartera total.
2. Fuente exacta del 6,5% real "prudente" — tratado como supuesto del equipo, no cifra publicada.
3. Confianza numérica de Ω en Black-Litterman: se usó el método estándar (He & Litterman 1999)
   proporcional a τΣ, no una calibración empírica de las vistas.
4. ~~El Solver de Excel real queda pendiente~~ — RESUELTO: ejecutado por el cliente en ambas hojas,
   confirma exactamente los pesos de scipy.optimize (ver sección G).

## N. Resultado

**NEXUM FINAL VALIDATION: PASS** (12/12 comprobaciones automáticas superadas, ver
`validar_modelo_final.py`).
