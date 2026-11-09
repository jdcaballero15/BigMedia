# Unidad: Facturación con descarga en Excel

- **Estado:** en curso · **Épica:** E11 Facturación mensual · **App dueña:** facturacion
- **Origen:** HU-060 (ajuste) y HU-070, del PR `docs/historias-facturacion-planilla` · **Rama:** `feature/facturacion-descarga-excel`

## Objetivo

Que la pantalla «Ítems a facturar» pase a llamarse «Facturación», que cada ítem se cargue como
una fila con los siete datos de la planilla de Administración y que Seba pueda descargar en Excel
los ítems de la lista para pasárselos a Administración, sin enviar el mes.

## Decisiones tomadas con Juan Diego (09/11/2026)

- **Nombre:** «Facturación» en el menú, el título de la pantalla y la ruta de arriba.
- **Los siete datos:** cliente (razón social), importe neto total, costos incluidos, detalle
  costo, tipo de venta, Gob/Priv y tipo. Son los únicos del formulario de «Nuevo ítem» y de
  edición, en ese orden (ajuste del 09/11/2026, tras la prueba en local: al principio quedaban
  arriba y el resto debajo). El mes de un ítem nuevo es el elegido en la lista.
- **Costos incluidos y detalle costo:** dos datos nuevos del ítem que se escriben a mano (un
  importe y un texto). No tocan el módulo de costos ni la rentabilidad.
- **Lista:** solo esas siete columnas, sin Estado. Al final de cada fila queda el menú de tres
  puntos (editar, facturar, anular, etc.), sin título de columna, para poder abrir el ítem.
- **Excel:** botón «Descargar Excel» con los ítems de la lista según los filtros, sin los
  anulados, solo con las siete columnas. No cambia el estado de ningún ítem.

## Cambios

- **Backend `facturacion`:**
  - `ItemFacturacion` suma `costos_incluidos` (`Decimal`, 14,2, opcional, no negativo, con su
    `CheckConstraint`) y `detalle_costo` (texto opcional).
  - El serializer los expone y los acepta, con las mismas reglas de edición del resto del ítem
    (un ítem Enviado o Facturado no se edita).
  - `services.py`: `COLUMNAS_DESCARGA`, con las siete columnas y los títulos de RN-024, y
    `planilla_de_lista_xlsx(items, mes)`. Arma el período (si hay filtro de mes) y el título
    arriba, una fila por ítem y abajo las sumas de importe y costos y el neto, como la planilla
    real. Los costos incluidos y el detalle salen del ítem; el tipo, del tipo de soporte.
  - `views.py`: acción `GET /api/facturacion/items/planilla/`, que reusa los filtros de la lista
    (mes, estado, cliente, campaña), excluye los anulados y responde el .xlsx. Pueden usarla
    todos los roles con sesión, también Lectura.
  - Migración nueva que solo agrega las dos columnas.
- **Frontend `features/facturacion`:**
  - `App.tsx`: el ítem del menú pasa a «Facturación».
  - `ItemsPage.tsx`: el título pasa a «Facturación». La tabla muestra solo las siete columnas más
    el menú de tres puntos, y suma el botón «Descargar Excel», que arma la URL con los filtros
    actuales.
  - `ItemForm.tsx` y `types.ts`: solo los siete datos, en orden, con los dos campos nuevos. Salen
    del formulario el mes, la campaña, el CUIT, la marca, el tipo de servicio, la descripción, el
    período, la cantidad, el precio, la alícuota, la orden de compra (número, fecha y PDF), los
    costos del ítem y las notas. Al editar solo viajan los siete datos, así que lo que un ítem ya
    tenga no se pisa. La página deja de cargar marcas y campañas.
- **Manual de uso:** la sección de ítems a facturar pasa a «Facturación» y explica la descarga.

**Fuera de alcance:** no cambian «Enviar a facturar» ni su planilla (HU-066), los totales del mes,
el módulo de costos ni el backend de la orden de compra y de los costos del ítem (HU-062, HU-063):
solo dejan de cargarse desde esta pantalla. Los componentes `PdfOrdenCompra` y `CostosDelItem`
quedan sin uso en la pantalla y no se borran en esta unidad.

## Migraciones

`facturacion/0009`: agrega `costos_incluidos` y `detalle_costo` a `ItemFacturacion`, más la
restricción de no negativo. No mueve datos: los ítems existentes quedan con esos datos vacíos.

## Reglas provisorias que se usan

- RN-024 (`provisoria`): las siete columnas de la planilla real, en su orden, con el período
  arriba y los totales y el neto abajo.

## Cómo se prueba

- Backend (pytest, contra PostgreSQL):
  - Se guarda un ítem con costos incluidos y detalle, y se leen tal cual; un importe negativo se
    rechaza; guardarlo no crea ni cambia ningún costo.
  - La descarga tiene solo las siete columnas, en orden, con los valores del ítem, el período
    arriba y los totales abajo (`@pytest.mark.regla("RN-024")`).
  - Respeta los filtros de mes y estado, excluye los anulados, no cambia el estado de los ítems,
    funciona con la lista vacía y la puede usar Lectura.
- Frontend (Vitest): el menú y el título dicen «Facturación»; la tabla tiene solo las siete
  columnas; el formulario tiene solo los siete datos, manda el mes elegido en un ítem nuevo y no
  lo cambia al editar; «Descargar
  Excel» apunta a la URL con los filtros actuales. La cobertura se mantiene ≥ 80 %.
- Prueba manual en local: cargar un ítem nuevo, filtrar por mes, descargar el Excel y abrirlo.

## Registro de gates

- Gate 1 (plan): 2026-11-09 — aprobado por Juan Diego
- Gate 2 (verificación, primera corrida, antes del ajuste del formulario): 2026-11-09 — corrida, pendiente de aprobación de Juan Diego tras probarlo en local. ruff format y check sin observaciones (148 archivos); mypy sin errores (148 archivos); sin migraciones pendientes; pytest 952 tests contra PostgreSQL, ninguno salteado, cobertura 97,37 %; pre-commit (incluye gitleaks) sin hallazgos; frontend format, lint, typecheck y build OK, 416 tests, cobertura 92,81 % sentencias / 94,82 % líneas.
- Gate 2 (verificación, tras el ajuste del formulario): 2026-11-09 — corrida, pendiente de aprobación de Juan Diego tras probarlo en local. Sin cambios en el backend desde la primera corrida (952 tests, cobertura 97,37 %); pre-commit (incluye gitleaks) sin hallazgos; frontend format, lint, typecheck y build OK, 405 tests, cobertura 92,74 % sentencias / 94,75 % líneas.
- Gate 3 (PR): pendiente
