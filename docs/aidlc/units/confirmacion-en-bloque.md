# Unidad: Confirmación en bloque

- **Estado:** en revisión · **Épica:** E10 Armado de campañas y reserva masiva · **App dueña:** `reservas`
- **Origen:** HU-059, más los criterios 3 y 4 de HU-058 · **Rama:** `feature/reservas-confirmacion-en-bloque`

## Objetivo

Cerrar el armado de una campaña en un paso: "Confirmar reservas" confirma todas sus Pendientes
que entran y lista los conflictos de las que no, con cartel, fechas y la campaña que ocupa el
cupo. Además, cuando cambian las fechas de la campaña, el sistema ofrece mover las Pendientes a
las fechas nuevas sin tocar las Confirmadas. Es la última de las tres unidades de E10. La rama sale de la de
[reserva-masiva](reserva-masiva.md) (PR #76), porque toca los mismos archivos de `reservas`.

## Decisiones

1. **Criterios 1 y 2 de HU-059 ya están hechos:** `campanias/services.py::validar_confirmacion`
   (RN-011) ya exige cliente, marca y fechas para confirmar, y deja guardar una Cotizada
   incompleta. Esta unidad no los toca; solo suma un test del recorrido.
2. **Confirmar reservas exige la campaña Confirmada** (propuesta): el botón aparece solo si la
   campaña está Confirmada y tiene Pendientes. Si no, la API responde 400 con "Primero confirmá la
   campaña". Así se sigue el orden de la historia: primero la campaña, después sus reservas. La
   confirmación individual de una reserva sigue como hoy.
3. **Cada Pendiente, en su propia transacción** (HU-034): `select_for_update()` sobre el cartel,
   pasa a Confirmada y `validar_disponibilidad`. Si no entra, se revierte y queda Pendiente.
   Es el mismo camino que la confirmación individual y la auditoría registra el cambio de estado
   con el usuario, igual que el `PATCH`. Las Pendientes se procesan en orden de creación.
4. **Conflictos estructurados** (propuesta): la validación pasa a exponer las reservas en
   conflicto, además del mensaje. Así el resumen lista, por cada Pendiente que no entró, el
   cartel, sus fechas y las campañas que ocupan el cupo (criterio 3). El mensaje del `PATCH`
   individual no cambia.
5. **Reintentar es natural** (criterio 5): "Confirmar reservas" procesa solo lo que sigue
   Pendiente. No hace falta clave de idempotencia.
6. **Mover las Pendientes al cambiar las fechas** (HU-058, criterios 3 y 4; propuesta):
   - Al guardar fechas nuevas en una campaña con Pendientes, la pantalla pregunta "¿Actualizar
     las N reservas Pendientes a las fechas nuevas?".
   - Si se acepta, `POST /api/reservas/reservas/mover-pendientes/` con la campaña y las fechas
     anteriores. Mueve **solo las Pendientes que tenían exactamente las fechas anteriores de la
     campaña**: una tanda que se cargó con otras fechas a propósito no se pisa. Las Confirmadas,
     Finalizadas y Canceladas no se tocan.
   - El movimiento va en `reservas`, porque `campanias` no puede importar de `reservas`. Por eso
     se hace en un segundo pedido, después de guardar la campaña. Si ese pedido falla, la
     pantalla lo avisa y el mismo pedido se puede repetir sin efectos dobles.
   - Mover una Pendiente no valida cupo, como cualquier edición de una Pendiente (RN-002). El
     nombre se regenera si cambia el mes.
7. **Fuera de alcance:** cancelar en bloque y mover Confirmadas (que exigiría revalidar cupo,
   HU-031).

## Cambios

- `reservas/services.py`:
  - `conflictos_de(reserva)` devuelve las reservas que ocupan el cupo en el día pico, o una lista
    vacía. `validar_disponibilidad` la usa para armar su mensaje, que no cambia.
  - `confirmar_reservas_de_campania(campania, usuario)` devuelve las confirmadas y los conflictos
    (reserva, cartel, fechas, campañas que ocupan).
  - `mover_pendientes(campania, inicio_anterior, fin_anterior)` devuelve las movidas.
- `reservas/views.py`: acciones `confirmar-en-bloque` y `mover-pendientes` en `ReservaViewSet`,
  con los permisos de reservas.
- Frontend:
  - En `ReservasCampania`, el botón "Confirmar reservas" con el resumen de confirmadas y la
    lista de conflictos.
  - En `CampaniasPage`, después de guardar fechas nuevas con Pendientes en esas fechas, la
    pregunta y el movimiento.
  - En el detalle, se recargan el seguimiento y la lista.

## Migraciones

Ninguna.

## Reglas provisorias que se usan

- RN-011: confirmar la campaña exige cliente, marca y fechas (ya implementado).
- RN-001, RN-002 y RN-003: los aplica `validar_disponibilidad` al confirmar cada reserva.

## Cómo se prueba

- `backend/tests/test_confirmacion_en_bloque.py`:
  - 200 Pendientes, 190 libres y 10 en conflicto (criterio 3): 190 Confirmadas, 10 Pendientes y
    cada conflicto con cartel, fechas y campaña que ocupa.
  - Dos campañas confirman a la vez el último cupo del mismo cartel (criterio 4, con hilos y
    PostgreSQL real): una queda Confirmada y la otra Pendiente con su conflicto
    (`@pytest.mark.regla("RN-003")`).
  - Repetir solo procesa lo que sigue Pendiente (criterio 5).
  - Campaña no Confirmada: 400. Usuario de Lectura: 403.
  - El cambio de estado queda auditado con el usuario.
  - Pico diario en un LED (`@pytest.mark.regla("RN-003")`) y Pendientes de otras campañas según
    el parámetro (`@pytest.mark.regla("RN-002")`).
- `backend/tests/test_mover_pendientes.py`:
  - Mueve solo las Pendientes con las fechas anteriores y regenera el nombre (criterio 3).
  - Las Confirmadas no cambian (criterio 4).
  - Repetir no hace nada más.
  - Pedido inválido: 400. Usuario de Lectura: 403.
- Criterios 1 y 2 de HU-059: ya los cubren `test_confirmar_exige_marca_cliente_y_fechas` y
  `test_crear_campania_sin_datos_se_guarda` en `backend/tests/test_campanias.py`.
- Frontend: botón visible solo con la campaña Confirmada y Pendientes, resumen con conflictos,
  pregunta al cambiar fechas (aceptar y rechazar) y aviso si falla el movimiento.

## Registro de gates

- Gate 1 (plan): 2026-10-27 — aprobado por Gonza
- Gate 2 (verificación): 2026-10-27 — `ruff format --check` (123 archivos) y `ruff check`
  sin errores; `mypy backend` sin errores (123 archivos); `makemigrations --check` sin cambios;
  `pytest --cov`: 610 tests en verde (incluida la concurrencia con dos hilos), coverage 96,44 %;
  frontend `format:check`, `lint`, `typecheck` y `build` en verde, `test:coverage` con 266 tests
  en verde y 92,76 % de líneas (90,06 % de sentencias); `pre-commit run --all-files` en verde.
  Espera revisión de Gonza o Juan Diego.
- Gate 3 (PR): #78, pedido por Gonza el 2026-10-27
