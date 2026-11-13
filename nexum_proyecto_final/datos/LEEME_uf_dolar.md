# UF y dólar observado 2013-2026 (mindicador.cl)

Fuente: API pública de mindicador.cl, una llamada por año
(`https://mindicador.cl/api/uf/AAAA` y `https://mindicador.cl/api/dolar/AAAA`).
Descarga hecha el 2026-11-13.

| Archivo | Filas | Primera fecha | Última fecha |
|---|---|---|---|
| `uf_diaria_2013_2026.csv` | 4.724 | 2013-01-01 | 2026-12-09 |
| `uf_mensual_2013_2026.csv` | 156 | 2013-01-31 | 2026-12-09 |
| `dolar_observado_diario_2013_2026.csv` | 3.202 | 2013-01-02 | 2026-11-13 |
| `dolar_observado_mensual_2013_2026.csv` | 155 | 2013-01-31 | 2026-11-13 |

- Columnas: `fecha` (YYYY-MM-DD, fecha en Chile) y `valor` (pesos).
- Las series diarias están ordenadas por fecha y sin fechas duplicadas.
- Las series mensuales guardan el último valor disponible de cada mes. Para el último mes de cada serie (UF dic-2026, dólar nov-2026) es un valor parcial.
- La UF llega hasta 2026-12-09 porque se publica por adelantado.

## Huecos conocidos (datos faltantes)

| Serie | Último dato antes del hueco | Primer dato después | Días sin dato | Año faltante |
|---|---|---|---|---|
| UF | 2020-12-31 | 2022-01-01 | 365 | 2021 completo |
| Dólar observado | 2019-12-30 | 2021-01-04 | 370 | 2020 completo |

Por eso tampoco hay filas mensuales de UF para 2021 (12 meses) ni de dólar para 2020 (12 meses).

**Causa:** mindicador.cl no entregó esas dos llamadas (`/api/uf/2021` y `/api/dolar/2020`). Entre las 17:45 y las 19:30 del 13-11-2026 se intentaron más de 10 veces cada una, en serie y espaciadas. Siempre devolvieron error del servidor: 502 Bad Gateway, 500 "cursor id not found", respuesta vacía o conexión reseteada. Los otros 26 años se descargaron sin problemas.

Fuera de esos huecos, la UF no tiene ningún hueco de más de 7 días. Los únicos otros huecos del dólar son de 5 días, en Fiestas Patrias (2013, 2018, 2019 y 2024), porque el dólar observado no se publica en feriados ni fines de semana.

Para completar, hay que volver a descargar `/api/uf/2021` y `/api/dolar/2020` y regenerar los CSV.
