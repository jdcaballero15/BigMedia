# Unidad: ajuste-reporte-ocupacion-por-formato

- **Estado:** en revisión · **Épica:** E8 Reportes y paneles · **App dueña:** reservas
- **Origen:** pedido de Juan Diego (2026-11-20), ajuste de HU-048 · **Rama:** `feature/reservas-ocupacion-por-formato`
- **Depende de:** el merge del PR `docs/historias-ocupacion-por-formato` (#154, mergeado).

## Objetivo

En **Reportes › Ocupación**, reemplazar los filtros de departamento y modalidad por un filtro de
formato de cartel, y mostrar las cifras de arriba y la evolución mes a mes por formato en lugar de
digital y fija.

## Decisiones (Juan Diego, 2026-11-20)

1. **Un formato o Todos.** Una lista desplegable con «Todos» por defecto, como en Carteles.
2. **Resumen por formato.** Las cifras de arriba y la tabla «Evolución por modalidad» pasan a
   agruparse por formato. Como cada formato tiene una sola modalidad, se sigue sin promediar fijos
   con LED (regla de HU-048).
3. **Se reemplaza también en el servidor.** `GET /api/reservas/reporte-ocupacion/` deja de aceptar
   `zona` y `modalidad` y acepta `formato`. Queda una sola forma de filtrar.

## Requisito previo: PR de historias

El criterio 3 de HU-048 dice «segmentable por modalidad y zona», y la regla dice «por defecto se
muestran separados por modalidad». Antes del código va un PR `docs/historias-ocupacion-por-formato`
que cambie el criterio 3 a «segmentable por formato», la regla a «separados por formato (cada
formato tiene una sola modalidad, así que nunca se promedian fijos con LED)» y sume su fila en
`registro-de-cambios.md`. No cambia ninguna regla RN.

## Cambios

- `reservas`, `services.reporte_ocupacion`: el parámetro `formato: int | None` reemplaza a `zona`
  y `modalidad`. `_totales_por_modalidad` pasa a `_totales_por_formato`: una entrada por formato
  con carteles en el reporte, con `formato` (id), `nombre`, `modalidad`, `ocupacion` y `por_mes`,
  ordenada por nombre. La respuesta cambia la clave `modalidades` por `formatos`. Cada fila de
  cartel conserva `modalidad`, `zona_nombre` y `formato_nombre`.
- `reservas`, `views.ReporteOcupacionView`: lee `formato` (id positivo, con el mismo validador que
  usaba `zona`) y deja de leer `zona` y `modalidad`.
- `frontend`, `features/reservas/ReporteOcupacion.tsx` y `ocupacion.ts`:
  - Se quitan los selectores de **Departamento** y **Modalidad**; se suma **Formato** (carga
    `/api/inventario/formatos/`, «Todos» por defecto).
  - Cifras de arriba: una por formato con su ocupación del período, más «Carteles en el reporte».
    La primera (mayor ocupación) va en azul, como hoy.
  - «Evolución por modalidad» pasa a «Evolución por formato», una fila por formato.
  - Mapa de calor y ranking: sin cambios.
  - CSV y PDF: el texto de filtros muestra «Formato: …» en lugar de departamento y modalidad; las
    columnas suman **Formato** (ya viene en cada fila).
- `docs/manual/manual-de-uso.md`: el párrafo del reporte de Ocupación.

## Migraciones

Ninguna.

## Reglas provisorias que se usan

- RN-004 (capacidad por cartel; una reserva = un cupo), sin cambios: los días-cupo se siguen
  midiendo con la capacidad real de cada cartel.

## Cómo se prueba

- Backend (`backend/tests/test_reporte_ocupacion.py`):
  - `test_reporte_ocupacion_filtro_formato_solo_ese_formato`
  - `test_reporte_ocupacion_totales_por_formato_sin_mezclar_modalidades`
  - `test_reporte_ocupacion_formato_invalido_400`
  - `test_reporte_ocupacion_ignora_zona_y_modalidad` (ya no filtran)
  - Los tests actuales de `zona` y `modalidad` se reemplazan por los de formato.
- Frontend (`ReporteOcupacion.test.tsx`): no hay selectores de departamento ni de modalidad; elegir
  un formato pide `?formato=<id>`; las cifras y la evolución muestran un renglón por formato; el
  texto de filtros del PDF dice «Formato: LED».
- Definition of Done completa de `CLAUDE.md` §7.

## Registro de gates

- Gate 1 (plan): aprobado — Juan Diego (2026-11-24)
- Gate 2 (verificación): hecho (2026-11-24) — ruff, mypy, makemigrations, pytest 930 con 97,6 % de coverage, frontend 444 tests y build, pre-commit con gitleaks, todo en verde
- Gate 3 (PR): pedido por Juan Diego (2026-11-24)
