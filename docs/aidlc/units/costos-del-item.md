# Unidad: Costos del ítem y neto final

- **Estado:** en revisión · **Épica:** E11 Facturación mensual · **App dueña:** `facturacion`
  (con cambios en `costos`)
- **Origen:** HU-063, HU-066 criterio 1 · **Rama:** `feature/facturacion-costos-del-item`

## Objetivo

Cada ítem a facturar puede tener costos (comisión, proveedor, impresión), fijos o en porcentaje
del neto, y muestra su costo total y su neto final. El listado del mes y la planilla suman costos
y neto final (HU-066, criterio 1). Los costos son los mismos registros del módulo `costos`: se
cargan una sola vez.

## Decisiones

1. **El vínculo vive en `facturacion`** (decisión de Gonza del 27/10/2026): `costos` no puede
   importar de `facturacion` (tabla de dependencias de `CLAUDE.md`).
   - `costos.Costo.reserva` pasa a opcional. Un costo pertenece a una reserva o a un ítem.
   - `facturacion` tiene `CostoDeItem` (ítem y costo, uno a uno por costo), que une el ítem con
     sus costos. No hace falta un ADR: la tabla de dependencias no cambia.
   - El servicio de `facturacion` es el único que crea costos sin reserva, y siempre con su
     vínculo, en la misma transacción.
2. **Costo en porcentaje** (criterios 1 y 3): `Costo` suma `porcentaje` (opcional). Si lo tiene,
   el monto es ese porcentaje del neto del ítem, redondeado al centavo, y se recalcula cuando
   cambia el neto. El monto se sigue guardando, así los reportes de `costos` no cambian.
3. **Tipo y destinatario**: `Costo.Tipo` suma `comision`. "A quién se le paga" es el proveedor si
   lo es, o un texto libre nuevo, `destinatario`.
4. **Costos de reserva vinculados** (criterio 4): si el ítem tiene campaña, se puede vincular un
   costo ya cargado en una reserva de esa campaña, sin copiarlo. Así la rentabilidad de la
   campaña lo cuenta una sola vez (desde la reserva). Los costos propios del ítem, sin reserva,
   no entran en la rentabilidad de la campaña: `costos` no conoce ítems.
5. **Anulación**: igual que hoy, un costo se anula con motivo y deja de sumar. No se borra.
6. **Totales** (criterio 5): `totales_del_mes` suma costos y neto final de los ítems no anulados.
   La planilla agrega "Costos" y "Neto final" al final (RN-024).

## Cambios

- `costos/models.py`: `reserva` opcional, `porcentaje`, `destinatario` y el tipo `comision`.
- `facturacion/models.py`: `CostoDeItem`. `facturacion/services.py`: alta, vínculo, recálculo
  por neto, costo total y neto final del ítem, y totales del mes.
- API: `GET` y `POST /api/facturacion/items/<id>/costos/`,
  `POST /api/facturacion/items/<id>/costos/vincular/` y la anulación con motivo. El ítem expone
  `costo_total` y `neto_final`.
- Frontend: sección "Costos" en `ItemForm`; costos y neto final en el listado y los totales de
  `ItemsPage`.

## Migraciones

Dos: en `costos`, `reserva` opcional y los campos nuevos (sin mover datos; los costos actuales
quedan iguales); en `facturacion`, `CostoDeItem`.

## Reglas provisorias que se usan

- RN-024: las columnas Costos y Neto final van al final.

## Cómo se prueba

- `backend/tests/test_costos_del_item.py`: 15 % de 10000 da 1500 y neto final 8500 (criterio 1);
  fijo se resta tal cual (criterio 2); cambiar el neto recalcula los porcentuales (criterio 3); un
  costo de reserva vinculado cuenta una vez en la rentabilidad de la campaña (criterio 4); totales
  del mes iguales a la suma manual, sin anulados (criterio 5).
- `backend/tests/test_costos.py`: los costos de reserva siguen funcionando igual.
- Planilla: columnas Costos y Neto final (`@pytest.mark.regla("RN-024")`).
- Frontend: `ItemForm.test.tsx` e `ItemsPage.test.tsx`.

## Registro de gates

- Gate 1 (plan): 2026-10-27 — aprobado por Gonza
- Gate 2 (verificación): 2026-10-27 — `ruff format --check` (134 archivos) y `ruff check` sin
  errores; `mypy backend` sin errores (134 archivos); `makemigrations --check` sin cambios;
  `pytest --cov`: 743 tests en verde, coverage 96,86 %; frontend `format:check`, `lint`,
  `typecheck` y `build` en verde, `test:coverage` con 324 tests en verde y 93,62 % de líneas
  (91,15 % de sentencias); `pre-commit run --all-files` en verde. Aprobado por Gonza el
  2026-10-27, con estas decisiones: los costos se cargan, vinculan y anulan solo con el ítem en
  Borrador; un costo de reserva vinculado se anula desde Costos; un porcentaje sin neto da 0; el
  neto final del mes es el neto menos los costos.
- Gate 3 (PR): #82, pedido por Gonza el 2026-10-27
