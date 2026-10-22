# Unidad: Reservas base

- **Estado:** mergeada · **Épica:** E5 Reservas y motor de disponibilidad · **App dueña:** `reservas`
- **Origen:** HU-028, HU-029, HU-030, HU-035, HU-037, HU-040 · **Rama:** `feature/reservas-base`

## Objetivo

Permitir crear, editar, nombrar y mover entre estados las reservas (la intersección Campaña × Cartel),
con el precio estampado y la ocupación del cartel calculada al momento. Es la primera mitad de E5: deja
las reservas listas para que la segunda unidad agregue la validación dura de solapamiento y la
concurrencia (HU-031…HU-034).

## Alcance y división de E5

E5 se parte en dos unidades (decisión de Juan Diego, 2026-10-19):

- **Reservas base (esta unidad):** HU-028, HU-029, HU-030, HU-035, HU-037, HU-040.
- **Motor de disponibilidad (unidad siguiente):** HU-031 (solapamiento), HU-032 (mensaje de conflicto),
  HU-033 (config de borde/tentativa), HU-034 (concurrencia). Más adelante: HU-036 (finalizar auto),
  HU-038 (import histórico), HU-039 (fuera de servicio).

> **Riesgo asumido.** Hasta que exista el motor, confirmar una reserva **no** valida solapamiento: se
> puede sobrevender. Esta unidad no debe usarse en producción real sin la unidad del motor. Se marca
> explícito en la interfaz y en el `README`/plan.

## Cambios

- `reservas` (app nueva): modelo `Reserva`, serializer, viewset (sin DELETE), servicio para el nombre y
  las transiciones de estado, rutas bajo `/api/reservas/`, migración inicial + permisos al grupo
  Operativo. Importa de `inventario` (Cartel) y `campanias` (Campania); **no** importa `costos` ni
  `facturacion`.
- `config`: registrar `apps.reservas` y montar sus urls.
- `frontend/src/features/reservas/`: `ReservaForm` (alta/edición) y la lista de reservas dentro del
  **hub de la campaña** (`CampaniaDetalle`), que deja de mostrar "Reservas próximamente". La campaña
  viene preseleccionada al agregar desde ahí (HU-028 criterio 4).

### Modelo `Reserva`

| Campo | Tipo | Regla |
| --- | --- | --- |
| `campania` | FK `campanias.Campania` (PROTECT) | Obligatoria. |
| `cartel` | FK `inventario.Cartel` (PROTECT) | Obligatorio (HU-028). |
| `fecha_inicio` / `fecha_fin` | DateField | Obligatorias; `fecha_fin` ≥ `fecha_inicio` (HU-028). |
| `estado` | TextChoices | `pendiente` (default) · `confirmada` · `finalizada` · `cancelada`. |
| `precio_alquiler` | DecimalField | Se precarga de `cartel.tarifa_lista`, editable, estampado (HU-029). |
| `precio_impresion` / `precio_fijacion` | DecimalField | A mano, por defecto 0; no negativos. |
| `total` | DecimalField (solo lectura) | Suma de los tres precios, calculada al guardar (HU-029). |
| `nombre` | CharField (solo lectura) | Generado "Marca - Cartel - Mes Año" (HU-030). |
| `creado_en` / `actualizado_en` | DateTime | `auto_now_add` / `auto_now`. |

- **Dinero con `Decimal`** siempre (regla absoluta #5), nunca `float`.
- **Nombre (HU-030):** marca de la campaña o "Sin marca"; cartel por su `nombre_visible`; mes y año de
  `fecha_inicio`. Se regenera al cambiar marca, cartel o fechas.
- **Estados (HU-035):** transiciones válidas `pendiente→confirmada|cancelada`,
  `confirmada→finalizada|cancelada`, `cancelada→confirmada`, `finalizada` no reactiva. Las inválidas se
  rechazan. **La revalidación de cupo al confirmar/reactivar se difiere a la unidad del motor**; acá la
  transición se permite sin validar solapamiento (ver riesgo).
- **Cancelar (HU-037):** cambia estado a `cancelada`, nunca borra; sin `DELETE` en la API.
- **Ocupación (HU-040):** solo lectura, calculada al consultar el cartel: cupos vigentes
  (reservas que ocupan cupo hoy, estado ≠ cancelada) sobre `cartel.capacidad`. Es display, no bloqueo.

### API

- `/api/reservas/reservas/`: `GET` (lista), `POST`, `GET/PATCH {id}`. `DELETE` → 405.
- Permiso compartido `config.permisos.LecturaConSesionEdicionOperativo`.
- Filtros de lista: `campania`, `cartel`, `estado`.
- Ocupación del cartel: se expone en la API de carteles o en un endpoint de solo lectura de `reservas`
  (a decidir en la implementación; sin tocar reglas de `inventario`).

## Migraciones

Una migración inicial: tabla `reserva` con FKs a `campania` y `cartel`, y una migración de datos que
otorga `view/add/change` de `Reserva` al grupo `Operativo` (patrón de las apps previas). No mueve datos.

## Reglas provisorias que se usan

- **RN-004** (LED: capacidad por cartel, una reserva = un cupo) y **RN-005** (séxtuples: slot genérico,
  sin posición) — esta unidad las respeta en el modelo (una reserva ocupa un cupo genérico). El conteo
  real por tramo es de la unidad del motor.
- **RN-006** (cancelar siempre se permite y libera el cupo) — se aplica en HU-037.
- **RN-001/RN-002/RN-003** (día de borde, tentativa, conteo por tramo) — **no** se aplican todavía: son
  de la unidad del motor.

## Cómo se prueba

- Backend (`backend/tests/test_reservas.py`, PostgreSQL real):
  - alta con campaña+cartel+fechas → 201; faltan cartel/fecha → 400; `fecha_fin` < `fecha_inicio` → 400
    (HU-028).
  - cartel inactivo o de baja → se rechaza (HU-028 criterio 3).
  - precio de alquiler se precarga del cartel y queda estampado aunque cambie la tarifa; total = suma;
    precio negativo → 400 (HU-029, con `Decimal`).
  - nombre generado y regenerado al cambiar marca/cartel/fecha; nunca vacío (HU-030).
  - transiciones válidas e inválidas de estado (HU-035); cancelar conserva el registro y no hay DELETE
    (HU-037, `@pytest.mark.regla("RN-006")`).
  - ocupación del cartel refleja las reservas vigentes al instante (HU-040).
  - anónimo/sin permiso no escriben; `DELETE` → 405; sin CSRF → 403.
- Frontend (Vitest): `ReservaForm` precarga el precio al elegir cartel y muestra errores de campo; el
  hub de campaña lista sus reservas y agrega una con la campaña ya seleccionada.

## Decisiones

- **División de E5 (Juan Diego, 2026-10-19):** dos unidades; esta es la base, el motor va después.
- **Flujo campaña→reserva (input de Seba):** la reserva se crea desde el hub de la campaña.

## Registro de gates

- Gate 1 (plan): 2026-10-19 — aprobado por Juan Diego.
- Gate 2 (verificación): 2026-10-19 — `ruff format --check` y `ruff check` sin errores; `mypy backend`
  sin problemas (66 archivos); `makemigrations --check` sin cambios; `pytest --cov` 170 pasan, total
  91.8 % (app `reservas` 97.7 %); frontend `format:check`/`lint`/`typecheck` OK, `test:coverage` 62
  pasan (líneas 89.5 %, sentencias 87.7 %), `build` OK; `pre-commit run --all-files` todo en verde
  (gitleaks sin hallazgos). Aprobado por Juan Diego.
- Gate 3 (PR): #16 (mergeado a develop el 2026-10-19).
