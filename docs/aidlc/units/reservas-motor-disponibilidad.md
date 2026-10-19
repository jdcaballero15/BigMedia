# Unidad: Reservas — motor de disponibilidad

- **Estado:** en curso · **Épica:** E5 Reservas y motor de disponibilidad · **App dueña:** `reservas`
- **Origen:** HU-031, HU-032, HU-033, HU-034 · **Rama:** `feature/reservas-motor-disponibilidad`

## Objetivo

Impedir la sobreventa: validar en el servidor, dentro de la misma transacción que guarda la reserva,
que un cartel tenga cupo libre en el rango pedido al **confirmar** (o editar una confirmada). Es el
objetivo central del proyecto (regla absoluta #7). Segunda y última mitad de E5.

## Alcance

- **HU-031** validación de solapamiento al confirmar (los 16 casos de la matriz del anexo).
- **HU-032** mensaje de conflicto que nombra cartel, cupos/capacidad, fechas y reservas en conflicto.
- **HU-034** garantía ante confirmaciones simultáneas (atómico por cartel, serializado).
- **HU-033** día de borde y tratamiento de la tentativa salen de configuración.

**Difiere a unidades posteriores:** HU-036 (finalizar vencidas por tarea programada), HU-038 (importar
reservas históricas), HU-039 completo (cartel fuera de servicio con reservas activas; esta unidad ya
rechaza reservar un cartel de baja, de la unidad base).

## Cambios

- `reservas/services.py`: motor `validar_disponibilidad(reserva, config)` + helpers de solapamiento y
  pico de ocupación; se corre dentro de `transaction.atomic()` con `select_for_update()` sobre el
  cartel (serializa por cartel; carteles distintos no se bloquean — HU-034).
- `reservas/serializers.py` / `views.py`: disparar la validación al pasar a `confirmada` o editar una
  confirmada cuando cambian fechas, cartel o estado; **no** revalidar si solo cambia un precio
  (matriz caso 13). Cancelar nunca valida (caso 14).
- `config` o `reservas`: parámetros de disponibilidad (día de borde, si la tentativa bloquea) leídos de
  `settings` con valores por defecto, overrideables en tests. La edición por pantalla (HU-001) queda
  fuera: acá es "sale de configuración" vía settings, no una UI de administración.
- Frontend: el `ReservaForm` ya existe; se agrega el manejo del error de conflicto (HU-032) mostrando
  el mensaje devuelto por el servidor (no genérico).

## Reglas (defaults provisorios que aplica)

- **RN-001 día de borde — inclusivo** (el día compartido se pisa): `1–15` y `16–30` no chocan; `1–15` y
  `15–30` sí. Configurable (HU-033).
- **RN-002 tentativa (pendiente)** — por defecto **solo visual**: la pendiente no cuenta para el bloqueo
  duro; configurable para que cuente (HU-033). La validación dura cuenta `confirmada` y `finalizada`
  siempre; `pendiente` según el parámetro; `cancelada` nunca.
- **RN-003 conteo de cupos en un rango — pico diario** (decisión de Juan Diego, 2026-10-19).

## Decisión resuelta — RN-003 (pico diario)

Se usa **pico diario** (ocupación máxima por tramo): exacto, no rechaza reservas que en realidad entran,
y coincide con el diseño ya mergeado en `units/base-del-repositorio.md`. El valor de RN-003 pasa de
"conteo simple" a "pico diario" en un **PR docs aparte** (`docs/historias-rn003-pico-diario`); este PR
de código solo actualiza su columna "Dónde vive".

## Migraciones

Ninguna (no cambia el modelo `Reserva`). Si la configuración se guardara en base en vez de `settings`,
habría una migración; el plan usa `settings`, así que no hay migración.

## Cómo se prueba

- Backend (`backend/tests/test_disponibilidad.py`, PostgreSQL real):
  - **Los 16 casos de la matriz del anexo de HU-031** (idéntico, contenido, contenedor, parcial izq/der,
    adyacentes según borde, separados, cancelada, tentativa según config, 12/20 permite, 20/20 bloquea,
    edición mueve fechas, edición solo precio no revalida, pasar a cancelada siempre, simultáneas,
    cartel no operativo). Cada caso de regla con `@pytest.mark.regla("RN-001/002/003")`.
  - **Concurrencia (HU-034):** ≥ 50 confirmaciones concurrentes sobre un cartel de capacidad 20 → nunca
    más de 20 superpuestas; sobre capacidad 1, una pasa y otra falla; carteles distintos no se serializan.
  - **Mensaje de conflicto (HU-032):** incluye cartel, cupos/capacidad, fechas y nombres; sin términos
    técnicos.
  - Día de borde y tentativa con `@override_settings` para los dos valores (HU-033).
- Frontend (Vitest): el `ReservaForm` muestra el mensaje de conflicto del servidor al fallar la confirmación.

## Registro de gates

- Gate 1 (plan): 2026-10-19 — aprobado por Juan Diego (RN-003 = pico diario).
- Gate 2 (verificación): 2026-10-19 — `ruff format --check`/`ruff check` sin errores; `mypy backend`
  sin problemas (67 archivos); `makemigrations --check` sin cambios; `pytest --cov` 193 pasan, total
  94.3 %, incluida la matriz de 16 casos de HU-031 y la concurrencia de HU-034 (capacidad 1: una pasa
  y una falla; 50 confirmaciones simultáneas en capacidad 20 → exactamente 20); frontend
  `format:check`/`lint`/`typecheck` OK, `test:coverage` 63 pasan (líneas 89.4 %), `build` OK;
  `pre-commit run --all-files` todo en verde. Esperando a Juan Diego.
- Gate 3 (PR): —
