# Insumos de Francisca para el informe oficial

Material rescatado del informe anterior de Francisca (ya reemplazado), adaptado al orden y a las cifras
oficiales de `Informe_Final_Nexum.docx` y `resultados/resultados_modelo.xlsx`. Para que Matías lo integre
donde corresponda. No trae cifras nuevas: toda cifra de abajo está en los resultados oficiales.

## 1. Narrativa para el cliente

### Pregunta que ordena el informe
María Ignacia y Tomás nos encargan USD 150.000 y un compromiso de USD 10.000 al año para responder una
pregunta concreta: **¿podemos pagar la universidad de Vicente y Emilia, comprar la casa del lago Villarrica
y dejarles una herencia, sin arriesgar lo primero por perseguir lo último?** Proponemos abrir el informe con
esta pregunta y cerrar cada sección respondiendo una parte de ella.

### Lo que define el caso (sugerido para 2.3 o 2.5)
La familia es rica en patrimonio inmobiliario y en capital humano, pero su patrimonio financiero es acotado
frente a sus metas. A la tasa libre de riesgo, sus recursos cubren solo 0,61 veces los objetivos: el plan es
factible únicamente si la cartera captura prima por riesgo. Esa tensión entre crecer y proteger lo urgente es
el hilo de toda la estrategia.

### Resumen ejecutivo en preguntas y respuestas (sugerido para la sección 1 y la presentación)

| Pregunta de la familia | Nuestra respuesta |
|---|---|
| ¿Cuánto necesitamos rentar? | 4,56% real anual (TIR requerida) |
| ¿Qué proponen? | Un núcleo pasivo (SPY, TLH, VCLT) de 69,4% y tres satélites con reglas: Low-Volatility 17,5%, Momentum en acciones 7,1% y Momentum en commodities 6,1%. Pesos de Black-Litterman; reserva de 4% fuera de la cartera |
| ¿Se cumplen los objetivos? | Educación, prácticamente siempre (~100%, en USD y en UF). Los tres objetivos: 96,0% con retornos 2013-2026 y 46,5% con supuestos prudentes |
| ¿Por qué tanta diferencia? | Con supuestos prudentes el retorno esperado (4,6% real) apenas iguala al requerido: Villarrica y la herencia quedan en el filo |
| ¿Qué podemos hacer nosotros? | Acordar desde ya el orden de ajuste. Herencia de USD 250 mil y Villarrica 25% menor llevan la probabilidad prospectiva de 46,5% a 74,8% |
| ¿Por qué no quedarnos con la AGF 85/15? | Rindió más en 2016-2026 (12,7% vs 9,9%), pero con más volatilidad, caídas más profundas y ~26% en tecnología, el mismo riesgo del empleo de Tomás (Nexum ~14%). Hacia adelante, Nexum da más probabilidad de éxito (45,3% vs 38,4% en UF) |

### Mensaje de cierre sugerido
"Educación está asegurada en todo escenario. Con la historia reciente, los tres objetivos se cumplen; con
supuestos prudentes, el retorno esperado apenas alcanza el requerido, y por eso proponemos acordar hoy las
palancas: primero la herencia, luego Villarrica, nunca Educación."

### Orden de prioridades y su justificación (responde a la crítica del profesor)
Educación → Villarrica → Herencia. Educación no admite sustitución ni postergación. Villarrica tiene fecha
(la jubilación), aunque el enunciado admite postergarla o reducirla. La herencia es la meta de mayor monto pero
sin fecha rígida: es la variable de ajuste natural y absorbe la variabilidad del mercado.

## 2. Respuestas a la retroalimentación del profesor

Mapa de cada crítica a dónde la responde el informe oficial. Sugerimos incluirlo como anexo breve o usarlo
como guion para la defensa.

| Crítica (Presentación 1 / Informe Parte I) | Cómo la responde la versión oficial | Sección |
|---|---|---|
| No se hizo Montecarlo (penalización −0,3) | Montecarlo en USD y UF, histórico y prospectivo, con probabilidad por objetivo y palancas | 4.2 |
| "Maximiza la probabilidad" sin cálculo | Se reportan 96,0% (histórico), 46,5% (prospectivo) y 74,8% con palancas | 1, 4.2, 7 |
| No se justifica la herencia sobre la propiedad | Orden Educación → Villarrica → Herencia, con justificación | 2.4 |
| No se calcula retorno requerido ni factibilidad | TIR requerida 4,56% real; cobertura de recursos 0,61 veces | 2.5 |
| Educación modelada como dos pagos únicos | Plan de desembolsos de 7 pagos anuales (años 14-20) | 2.4 |
| No se cuantifica riesgo-retorno ni se compara con la AGF | Métricas de la cartera y comparación con la AGF 85/15 | 2.7, 3.6 |
| Grable-Lytton respondido por ChatGPT | No se usan respuestas simuladas; el cuestionario se aplicará a los clientes | 2.3 |
| Casa de Santiago valorizada en "USD 30.000" | UF 30.000; solo UF 15.000 van a Villarrica | 2.4 |
| Sin literatura por estrategia | Fundamento y discusión crítica por estrategia | 3.2 |
| BAB mal implementado | Betting Against Beta eliminado | 3.3 |
| Filtros de momentum sin fundamento | Robustez de parámetros (umbrales, top-N, límites sectoriales) | 4.3 |
| Moneda funcional USD contradice metas en CLP/UF | USD justificado y simulaciones en UF; riesgo cambiario cuantificado | 3.4 |
| Benchmark: tasa Fed y ACWI inadecuados | Benchmark de política invertible por sleeve (SPLV, QMOM, mezcla de commodities) | 3.5 |
| TE de 4% sin justificar | TE objetivo = alfa / IR = 3%; máximo 4% | 3.7 |
| Backtest sobre 9 ETF sectoriales | Backtests point-in-time sobre las acciones del S&P 500 que se operan | 3.2, 4.1 |
| Sesgo de la ventana de 15 años | Sensibilidad por subperíodos y walk-forward fuera de muestra | 4.3 |

## 3. Pendientes que no resuelve este archivo
- Confirmar en el historial de StockTrak la comisión real por operación.
- Escribir la justificación de AFL (21-sep) o dejarla como desviación discrecional, como ya está en la sección 5.
- Aplicar el cuestionario de Grable-Lytton a los clientes.
