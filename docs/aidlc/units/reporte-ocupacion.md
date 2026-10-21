# Unidad: Reporte de ocupación (backend)

- **Estado:** en curso · **Épica:** E8 Reportes y paneles · **App dueña:** `reservas`
- **Origen:** HU-048 · **Rama:** `feature/reservas-reporte-ocupacion`

## Objetivo

Darle a gerencia la ocupación de los carteles medida en **días-cupo**, para identificar los soportes de
mejor y peor rendimiento (HU-048). Esta unidad entrega el cálculo y el endpoint; la pantalla (ranking,
evolución mensual y mapa de calor) va en una unidad de frontend aparte.

## Qué es la ocupación (HU-048)

- **Días-cupo ocupados / días-cupo disponibles**, con la capacidad real del cartel.
  - `disponibles(cartel, mes) = capacidad × días del mes dentro del período`.
  - `ocupados(cartel, mes) = Σ días que cada reserva que ocupa cupo (no cancelada) solapa con ese mes`,
    tope `disponibles` (una reserva = un cupo, RN-004).
  - `porcentaje = ocupados / disponibles × 100` (1 decimal; 0 si no hay días disponibles).
- Los séxtuples tienen capacidad variable y se tratan como los digitales (ya es así: capacidad por
  cartel).
- **Nunca se promedian carteles fijos con LED:** los totales (evolución mensual y total del período)
  se calculan **separados por modalidad**.

### Ejemplos de control (criterios de aceptación)

1. Cartel fijo capacidad 1, ocupado 15 de 30 días → 15 / (1×30) = **50 %**.
2. LED capacidad 20, 10 cupos ocupados todo el mes (30 días) → (10×30)/(20×30) = **50 %**.

## Decisiones de diseño (mi criterio — corregir acá si hace falta)

1. **Un solo endpoint** `GET /api/reservas/reporte-ocupacion/` cubre las tres vistas: la grilla
   cartel × mes es el mapa de calor, ordenar los carteles por su total es el ranking, y los totales
   por mes (por modalidad) son la evolución.
2. **Alcance backend**; la pantalla va en `reporte-ocupacion-frontend`.
3. **Período:** parámetros `desde`/`hasta` en `AAAA-MM` (por defecto, el año actual), tope de 12 meses
   como el calendario; valida formato y `desde ≤ hasta` → 400. Filtros opcionales `zona` y `modalidad`.
4. **Carteles:** solo los no dados de baja (`estado__es_baja=False`), como las demás vistas.
5. **Días del borde:** la ocupación cuenta los días de `[fecha_inicio, fecha_fin]` inclusive (lectura
   directa del ejemplo "15 de 30 días"); es una métrica de reporte, no el bloqueo de disponibilidad.
6. **Porcentajes** como número con 1 decimal; `dias_ocupados`/`dias_disponibles` como enteros.
7. **Permisos:** solo lectura con sesión (`LecturaConSesionEdicionOperativo`), como las demás vistas de
   reservas.

## Cambios

- `reservas/services.py`: `reporte_ocupacion(desde, hasta, zona=None, modalidad=None)` → arma, por cada
  cartel, las celdas por mes con `{periodo, porcentaje, dias_ocupados, dias_disponibles}` y su
  `ocupacion` total del período; ordena los carteles por `ocupacion` desc (ranking). Devuelve además
  `modalidades: [{modalidad, etiqueta, ocupacion, por_mes:[{periodo, porcentaje}]}]`, que **no mezclan
  modalidades** (evolución). Reusa el patrón de `calendario_disponibilidad` (una sola query de reservas
  agrupada por cartel). Respuesta: `{ periodos, carteles, modalidades }`.
- `reservas/views.py` + `urls.py`: `ReporteOcupacionView` (solo lectura) en
  `GET /api/reservas/reporte-ocupacion/` con los parámetros de arriba.

## Reglas que se usan

- **RN-004** (una reserva = un cupo; capacidad por cartel): se consume para el denominador y el conteo;
  ya vive en `inventario`/`reservas`. No se reubica. El test del cálculo lleva
  `@pytest.mark.regla("RN-004")`.

## Migraciones

Ninguna.

## Cómo se prueba

- Backend (`backend/tests/test_reporte_ocupacion.py`, PostgreSQL real):
  - cartel fijo capacidad 1 ocupado 15 de 30 días → 50 % (criterio 1, `@pytest.mark.regla("RN-004")`).
  - LED capacidad 20 con 10 cupos todo el mes → 50 % (criterio 2).
  - la grilla trae una celda por mes del período y el ranking ordena por ocupación desc.
  - los totales por modalidad no mezclan fijos con LED; una reserva cancelada no ocupa; filtros `zona`
    y `modalidad` acotan; `desde > hasta` y formato inválido → 400; anónimo → 401/403.

## Registro de gates

- Gate 1 (plan): 2026-10-21 — aprobado (alcance backend; días inclusive; totales separados por
  modalidad; solo lectura con sesión).
- Gate 2 (verificación): 2026-10-21 — `ruff format --check`, `ruff check`, `mypy backend` (87
  archivos), `makemigrations --check` y gitleaks en verde; `pytest --cov` 256 pasan (10 nuevos),
  cobertura total 94 % (umbral 80 %). Frontend no aplica (unidad backend).
- Gate 3 (PR): —
