# Unidad: Reserva masiva

- **Estado:** en revisión · **Épica:** E10 Armado de campañas y reserva masiva · **App dueña:** `reservas`
- **Origen:** HU-056, HU-057 · **Rama:** `feature/reservas-reserva-masiva`

## Objetivo

Desde una línea de formato de la campaña, abrir "Agregar carteles": la lista muestra los carteles
de ese formato con cupo libre en el rango, se filtran y se seleccionan en tanda, y al confirmar se
crea una reserva Pendiente por cada cartel elegido. La operación es idempotente y deja un resumen
de las creadas y las fallidas. Es la segunda de las tres unidades de E10. Depende de
[posiciones-por-formato](posiciones-por-formato.md) (PR #75): la rama sale de la de esa unidad y se
rebasa sobre `develop` cuando se mergee.

## Decisiones

1. **Qué es "cupo libre en el rango"** (propuesta): la lista usa la misma regla que la validación
   dura (HU-031). Esto implica pico diario (RN-003), día de borde (RN-001) y, según el parámetro
   "la tentativa ocupa cupo" (RN-002), contar o no las Pendientes. Con el default de RN-002
   (solo visual), un cartel con Pendientes de otra campaña aparece como libre, con una marca que
   lo avisa: "N tentativas". Así la lista y la confirmación (unidad siguiente) nunca se
   contradicen.
2. **Carteles ya reservados por la campaña** (propuesta): un cartel en el que la campaña ya tiene
   una reserva no cancelada que se solapa con el rango aparece como "ya en la campaña" y no se
   puede seleccionar. Así se evita duplicar una reserva sin querer.
3. **Idempotencia por clave natural** (propuesta): en una tanda, la reserva de un cartel se
   identifica por campaña, cartel, fecha de inicio y fecha de fin, entre las no Canceladas. Si
   ya existe, no se crea de nuevo y el resumen la informa como "ya existía". Así un reintento o
   una tanda repetida después de una falla dan el mismo resultado final (HU-057, criterios 4
   y 5), sin campo nuevo en el modelo. La contra es que no se pueden crear dos reservas iguales
   del mismo cartel en una tanda; una marca que quiera dos cupos del mismo LED o séxtuple
   (RN-004 y RN-005) los carga a mano, como hoy.
4. **Cada reserva, en su propia transacción** (propuesta): por cada cartel, `transaction.atomic()`
   con `select_for_update()` sobre el cartel, el mismo camino que el alta individual. Si una
   falla, las demás siguen. **Ajuste en la implementación (2026-10-27):** como en el alta
   individual, crear una Pendiente no valida cupo, aunque "la tentativa ocupa cupo" esté activo.
   Ese parámetro solo se aplica al confirmar (`necesita_validar_cupo` y
   `test_parametros_tentativa_bloquea_rige_en_la_siguiente_validacion`). La lista sí lo respeta
   al filtrar.
5. **Progreso por lotes desde la pantalla** (propuesta): la pantalla manda la selección en lotes
   de 25 carteles al endpoint de creación en bloque y muestra una barra "120 de 200". Cada lote
   devuelve creadas, ya existentes y fallidas con su motivo. Al terminar, el resumen ofrece
   "Reintentar fallidas", que manda solo esas (criterios 1, 3 y 4).
6. **Precio y nombre** (HU-057): el precio de alquiler es la tarifa de lista del cartel, con el
   mismo comportamiento que el alta individual: sin tarifa, 0, editable después. El nombre se
   autogenera ("Marca - Cartel - Mes", o "Sin marca"). La lista marca los carteles sin tarifa
   para que se note antes de confirmar.
7. **Fechas de la tanda** (HU-056): vienen de la campaña si las tiene; si no, la pantalla las
   pide. Se pueden ajustar siempre para la tanda. Sin fechas no se lista ni se crea nada (la API
   las exige).
8. **Filtros** (HU-056): zona, proveedor y dirección parcial. La búsqueda no distingue
   mayúsculas ni tildes: usa `direccion_busqueda`. Los carteles se identifican por
   `nombre_visible` (Dirección + Tamaño, o Dirección + Slots en séxtuples). Los carteles de baja
   no aparecen.
9. **Contador y aviso** (HU-056, criterios 5 y 6): el contador muestra "Gran Formato 60 de 100"
   (o solo "60 seleccionados" si la línea no tiene cantidad) y el monto estimado, que es la suma
   de las tarifas de lista con `Decimal` en el backend. La pantalla lo suma para mostrarlo, pero
   el importe que se guarda lo pone el servidor. Si la selección no coincide con lo solicitado,
   la confirmación avisa, pero deja seguir.
10. **Auditoría:** el alta individual de reservas hoy no se audita (solo los cambios), y la
    creación en bloque sigue igual.
11. **Fuera de alcance** (HU-056 y HU-057): autoselección, importación desde planilla, edición
    masiva de reservas ya creadas y confirmación en bloque (unidad `confirmacion-en-bloque`).

## Cambios

- `reservas/services.py`:
  - La lista reutiliza `_pico_en_rango`, el pico diario que ya usa el calendario, con el fin
    efectivo de RN-001. Da el mismo resultado que `validar_disponibilidad` sin duplicar la regla.
  - `carteles_para_tanda(campania, formato, desde, hasta, filtros)`: carteles no dados de baja de
    ese formato con cupo libre, más su `nombre_visible`, zona, proveedor, tarifa, la marca de
    tentativas y la marca "ya en la campaña". Trae las reservas del formato en el rango en una
    sola consulta, para que 200 o más carteles no generen una consulta por cartel.
  - `crear_reservas_en_bloque(campania, carteles, desde, hasta)`: devuelve creadas, ya
    existentes y fallidas (cartel y motivo).
- `reservas/views.py` y `urls.py`:
  - `GET /api/reservas/carteles-para-tanda/?campania=&formato=&desde=&hasta=&zona=&proveedor=&q=`
  - `POST /api/reservas/reservas/en-bloque/` con `{campania, fecha_inicio, fecha_fin, carteles: [ids]}`
    (hasta 50 por pedido). Los dos llevan los permisos de reservas.
- Frontend:
  - `features/reservas/AgregarCarteles.tsx`: fechas, filtros, tabla con selección,
    "Seleccionar todos los filtrados", contador y monto, aviso, progreso y resumen con
    "Reintentar fallidas".
  - En `PosicionesPorFormato`, un botón "Agregar carteles" por línea.
  - Al terminar una tanda se recargan el seguimiento y la lista de reservas de la campaña, con
    una revisión compartida en `CampaniaDetalle`.

## Migraciones

Ninguna.

## Reglas provisorias que se usan

- RN-001 (día de borde, inclusivo por default) y RN-002 (la Pendiente es solo visual por default)
  se leen de los parámetros, como en la validación.
- RN-003: pico diario.
- RN-004 y RN-005: una reserva ocupa un cupo, en un slot genérico.

## Cómo se prueba

- `backend/tests/test_carteles_para_tanda.py`:
  - Solo aparecen los carteles del formato con cupo libre en el rango (HU-056, criterio 1).
  - Pico diario en un LED de capacidad 2.
  - Pendientes de otra campaña: con el parámetro apagado, el cartel aparece libre y marcado; con
    el parámetro encendido, no aparece (`@pytest.mark.regla("RN-002")`).
  - Día de borde (`@pytest.mark.regla("RN-001")`).
  - Los filtros de zona, proveedor y dirección sin tildes se combinan (criterio 3).
  - Aparece la marca "ya en la campaña".
  - Los carteles de baja no aparecen.
  - Sin fechas, o con fechas invertidas, el pedido se rechaza (criterio 2).
  - La cantidad de consultas no crece con la cantidad de carteles.
- `backend/tests/test_reservas_en_bloque.py`:
  - Crea Pendientes con la tarifa de lista y el nombre autogenerado (HU-057, criterio 2).
  - Una tanda de 200 se crea en menos de un minuto (criterio 1).
  - Fallidas con motivo: cartel de baja o inexistente (criterio 3).
  - Reintentar no duplica nada (criterios 4 y 5).
  - Un usuario de Lectura recibe 403.
  - Un pedido de más de 50 carteles se rechaza.
  - Con el parámetro de RN-002 encendido, la tanda crea igual las Pendientes sobre un cartel
    lleno, como el alta individual (`@pytest.mark.regla("RN-002")`).
- Frontend `AgregarCarteles.test.tsx`:
  - Fechas precargadas, y fechas pedidas cuando la campaña no las tiene.
  - Filtros.
  - "Seleccionar todos los filtrados" y destildar (criterio 4).
  - Contador y monto (criterio 5).
  - Aviso por más o por menos (criterio 6).
  - Envío por lotes con progreso.
  - Resumen y reintento de las fallidas.

## Registro de gates

- Gate 1 (plan): 2026-10-27 — aprobado por Gonza
- Gate 2 (verificación): 2026-10-27 — `ruff format --check` (121 archivos) y `ruff check`
  sin errores; `mypy backend` sin errores (121 archivos); `makemigrations --check` sin cambios;
  `pytest --cov`: 589 tests en verde, coverage 96,41 %; frontend `format:check`, `lint`,
  `typecheck` y `build` en verde, `test:coverage` con 255 tests en verde y 92,49 % de líneas
  (89,81 % de sentencias); `pre-commit run --all-files` (gitleaks incluido) en verde.
  Espera revisión de Gonza o Juan Diego.
- Gate 3 (PR): #76, pedido por Gonza el 2026-10-27
