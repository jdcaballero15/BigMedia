# Unidad: Margen de campaña

- **Estado:** mergeada · **Épica:** E7 Costos y rentabilidad · **App dueña:** `costos`
- **Origen:** HU-025, HU-045 · **Rama:** `feature/costos-margen-campania`

## Objetivo

Mostrar en la campaña sus totales y rentabilidad: cantidad de reservas, ingreso (suma de los totales),
costo y margen, calculados desde sus reservas (sin las canceladas). Llena la sección "Costos y
rentabilidad" que quedó pendiente en el hub de campaña.

## Cambios

- `costos/services.py` + `views.py` + `urls.py`: endpoint de solo lectura
  `GET /api/costos/campania/?campania=<id>` → `{ cantidad_reservas, ingreso, costo, margen,
  porcentaje }`. `costos` ya importa `reservas`, así que agrega ambos (HU-025 monto/cantidad y HU-045
  margen) en una sola consulta; las reservas canceladas no suman.
- Frontend `features/campanias/CampaniaDetalle`: la sección "Costos y rentabilidad" consume el endpoint
  y muestra los totales (reemplaza el "próximamente").

### Reglas

- `ingreso` = suma de `reserva.total` de las reservas no canceladas (HU-025: el monto de la campaña).
- `cantidad_reservas` = conteo de reservas no canceladas (HU-025).
- `costo` = suma de los costos no anulados de esas reservas; `margen = ingreso - costo`;
  `porcentaje = margen/ingreso` o `null` si ingreso 0 (HU-045/HU-044).
- Las fechas de la campaña no se derivan de las reservas (HU-025): no se tocan.

## Migraciones

Ninguna.

## Reglas que se usan

- Reusa RN-006 (canceladas no suman) y el margen de HU-044.

## Cómo se prueba

- Backend (`backend/tests/test_margen_campania.py`): una campaña con varias reservas con costos da
  cantidad/ingreso/costo/margen correctos; una reserva cancelada no suma (HU-025/HU-045); sin ingreso
  no rompe ni da % inválido; campaña inexistente → 400; anónimo → 401/403.
- Frontend (Vitest): el hub de campaña muestra los totales de rentabilidad del endpoint.

## Registro de gates

- Gate 1 (plan): 2026-10-20 — aprobado por Juan Diego.
- Gate 2 (verificación): 2026-10-20 — ruff y mypy (78 archivos) OK, makemigrations --check sin cambios, pytest --cov 229 pasan (total 94.5%); frontend format/lint/typecheck OK, test:coverage 80 pasan, build OK; pre-commit en verde. Aprobado por Juan Diego.
- Gate 3 (PR): #23 (mergeado a develop el 2026-10-20).
