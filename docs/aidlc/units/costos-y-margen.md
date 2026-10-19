# Unidad: Costos y margen

- **Estado:** en curso · **Épica:** E7 Costos y rentabilidad · **App dueña:** `costos`
- **Origen:** HU-043, HU-044 (RN-007) · **Rama:** `feature/costos-costos-y-margen`

## Objetivo

Cargar líneas de costo en una reserva y ver su margen (ingreso, costo, margen, %). Alcance corto;
HU-045 (margen de campaña, necesita HU-025) y HU-046 (alquiler a terceros, Could/RN-007) se difieren.

## Cambios

- `costos` (app nueva; importa `reservas` e `inventario`): modelo `Costo`, serializer, viewset
  (list/create/patch, sin DELETE), endpoint de margen, migración + permisos al grupo Operativo.
- `config`: registrar `apps.costos` y montar urls en `/api/costos/`.
- Frontend `frontend/src/features/costos/`: panel `CostosReserva` (lista + alta de costo + margen),
  embebido en la lista de reservas de la campaña.

### Modelo `Costo`

| Campo | Tipo | Regla |
| --- | --- | --- |
| `reserva` | FK `reservas.Reserva` (PROTECT) | Obligatoria. |
| `tipo` | TextChoices | `alquiler` · `impresion` · `fijacion` · `otro`. Obligatorio (HU-043). |
| `proveedor` | FK `inventario.Proveedor` (PROTECT, null) | Destinatario del pago; opcional. |
| `monto` | DecimalField | Positivo (`Decimal`, regla #5). |
| `fecha` | DateField | Por defecto hoy. |
| `anulado` | Boolean | Baja lógica (no se borra); con `motivo`. |
| `motivo_anulacion` | CharField(blank) | — |

- Default RN-007: los costos son impresión y fijación (Big Media dueña; alquiler no se carga). No se
  fuerza el tipo: el servidor acepta los cuatro, el default comercial es informativo.

### API

- `/api/costos/costos/`: `GET` (filtra por `reserva`), `POST`, `GET/PATCH {id}`. `DELETE` → 405.
- `/api/costos/margen/?reserva=<id>`: `{ ingreso, costo, margen, porcentaje }` (HU-044).
  `ingreso = reserva.total`; `costo = suma de costos no anulados`; `margen = ingreso - costo`;
  `porcentaje = margen/ingreso` o `null` si ingreso 0. Costos anulados no suman (HU-043/044).
- Permiso `config.permisos.LecturaConSesionEdicionOperativo`.

## Migraciones

Una inicial: tabla `costo` + permisos `view/add/change` al grupo Operativo. No mueve datos.

## Reglas que se usan

- **RN-007** (propiedad de los carteles): default impresión/fijación; se actualiza su "Dónde vive".

## Cómo se prueba

- Backend (`backend/tests/test_costos.py`, PostgreSQL real): alta de costo asociado a la reserva;
  rechazo sin tipo/monto y monto no positivo; anulación no borra y no suma al margen; margen
  (1000 ingreso, 600 costo → 400 / 40%); sin ingreso no rompe ni da % inválido; sin costos margen =
  ingreso; `DELETE` → 405; anónimo/sin permiso no escriben.
- Frontend (Vitest): `CostosReserva` lista costos, agrega uno y muestra el margen.

## Registro de gates

- Gate 1 (plan): 2026-10-19 — aprobado por Juan Diego.
- Gate 2 (verificación): 2026-10-19 — ruff, mypy (77 archivos), makemigrations --check sin cambios, pytest --cov 217 pasan (total 94.2%); frontend format/lint/typecheck OK, test:coverage 72 pasan, build OK; pre-commit todo en verde. Aprobado por Juan Diego.
- Gate 3 (PR): —
