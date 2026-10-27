# Unidad: Ítems a facturar

- **Estado:** en revisión · **Épica:** E11 Facturación mensual · **App dueña:** `facturacion`
- **Origen:** HU-060, HU-061, HU-065 (RN-022, RN-023) · **Rama:** `feature/facturacion-items-a-facturar`

## Objetivo

Cargar los ítems a facturar a lo largo del mes, a medida que llegan las órdenes de compra, con el
neto, el IVA y el total calculados solos y un estado (Borrador, Enviado a facturar, Facturado o
Anulado). Reemplaza la planilla armada a mano. Es la primera unidad de E11 y entra en la entrega
del viernes 30/10. Le sigue `cierre-de-mes` (HU-066, "Enviar a facturar" y la planilla .xlsx).

## Decisiones

1. **E11 para el 30/10 en dos unidades** (Gonza, 27/10/2026): esta y `cierre-de-mes` (HU-066).
   Las Should (HU-062, HU-063, HU-064 y HU-067) van para el 04/11.
2. **Nada es obligatorio para guardar** (HU-060): igual que la campaña, todos los campos son
   opcionales. Los datos se exigen recién al enviar a facturar (HU-066, otra unidad). Hay una
   excepción: el mes de facturación arranca en el mes actual (criterio 2), aunque se puede cambiar
   o vaciar.
3. **Cálculo de importes, siempre con `Decimal`** (HU-061, CLAUDE.md regla 5):
   - El neto lo calcula el servidor como cantidad × precio unitario cuando no viene un neto
     explícito y hay cantidad y precio.
   - Un neto cargado a mano se respeta (criterios 2 y 3).
   - El IVA y el total se calculan siempre en el modelo, a partir del neto y la alícuota, y se
     redondean al centavo con `ROUND_HALF_UP`. No se pueden escribir desde la API.
   - La pantalla muestra el neto sugerido mientras se escribe, pero el que se guarda es el del
     servidor.
4. **Alícuota de IVA** (RN-023, provisoria): un porcentaje editable por ítem, con 21 % por
   defecto. No hay una lista cerrada de alícuotas hasta que responda Administración.
5. **Gob/Priv y tipo de venta F/V** (RN-023, propuesta): dos catálogos administrables, `Sector`
   y `TipoVenta`, igual que zonas y proveedores. Se cargan con Gobierno/Privado y F/V y se
   administran desde el admin de Django, sin pantalla propia por ahora.
6. **Tipo de soporte** (propuesta): un texto libre `tipo_soporte`, porque `facturacion` no
   puede importar de `inventario` y no conviene un ADR solo para esto. Desde una campaña se precarga con los formatos de sus líneas (por ejemplo
   "Gran Formato, LED") y se puede editar.
7. **Precargas en la pantalla** (criterios 3 y 4): al elegir un cliente se precarga su CUIT, y
   cambiarlo en el ítem no modifica al cliente. Al vincular una campaña se precargan su cliente
   que factura, su marca y el tipo de soporte. Precargar no pisa lo que ya se escribió. Sin
   campaña, todo se carga a mano (criterio 5).
8. **Estados y transiciones** (HU-065):
   - Los ítems nacen en Borrador.
   - Borrador pasa a Enviado a facturar solo con "Enviar a facturar", en la unidad
     `cierre-de-mes`.
   - Enviado a facturar pasa a Facturado, y para eso se exige el número de factura (criterio 2).
     Mientras no responda RN-022, lo hace el operativo.
   - Borrador y Enviado a facturar pasan a Anulado.
   - Facturado y Anulado son finales; corregir un facturado espera RN-026.
   - Un ítem Enviado, Facturado o Anulado no se edita, salvo para cambiar de estado. Reabrir es
     HU-067, para el 04/11.
9. **Sin borrado** (HU-006, criterio 4): la API no expone `DELETE`. Los ítems Anulados quedan
   visibles en el listado, pero no suman en los totales (criterio 3).
10. **Auditoría** (HU-007): quedan auditados los cambios de estado, número de factura, neto,
    alícuota y cliente, con el usuario, porque es el riesgo dominante de `facturacion`. También se
    guarda quién creó el ítem.
11. **Permisos** (propuesta): igual que campañas: el operativo crea y edita, y Lectura y
    Gerencia solo ven. Los reportes de ingresos siguen siendo de Gerencia; acá se ven ítems
    cargados, no ingresos agregados.

## Cambios

- `facturacion/models.py`:
  - `Sector` y `TipoVenta` (catálogos con `activo`), más una migración de datos con los valores
    iniciales.
  - `ItemFacturacion` con estos campos: `mes` (primer día del mes, opcional), `cliente`,
    `cuit_facturacion`, `marca`, `campania` (FK opcionales con `PROTECT`), `descripcion`,
    `periodo_desde`, `periodo_hasta`, `cantidad`, `precio_unitario`, `neto`,
    `alicuota_iva` (21,00 por defecto), `iva` y `total` (calculados), `tipo_servicio`
    (alquiler, impresión y colocación, otro), `tipo_soporte`, `sector`, `tipo_venta`, `notas`,
    `estado`, `numero_factura`, `creado_por`, `creado_en` y `actualizado_en`.
  - Restricciones: importes no negativos, alícuota entre 0 y 100, y período coherente.
- `facturacion/services.py`: cálculo de importes, transiciones de estado y validación del número
  de factura.
- `facturacion/serializers.py` y `views.py`:
  - CRUD sin `DELETE` en `/api/facturacion/items/`, filtrable por `mes` (AAAA-MM), `estado`,
    `cliente` y `campania`.
  - `GET /api/facturacion/items/totales/?mes=` devuelve neto, IVA y total del mes sin los
    anulados.
  - `GET /api/facturacion/catalogos/` devuelve sectores y tipos de venta activos.
- `facturacion/admin.py`: `Sector` y `TipoVenta` administrables. `ItemFacturacion` es de solo lectura, salvo que el superusuario puede borrar una carga errónea con auditoría, como en el resto de las apps (`SoloBorrarAdmin`, HU-006).
- Frontend `features/facturacion/`:
  - `ItemsPage.tsx`: lista por mes (por defecto el actual) con totales, filtro por estado y las
    acciones Anular y Marcar facturado (pide el número).
  - `ItemForm.tsx`: el formulario con las precargas y el neto sugerido.
  - Entrada "Ítems a facturar" en el menú.

## Migraciones

Dos nuevas en `facturacion`: una crea `Sector`, `TipoVenta` e `ItemFacturacion`, y la otra carga
los valores iniciales de los catálogos. No tocan datos existentes.

## Reglas provisorias que se usan

- RN-023: 21 % por defecto, editable; Gob/Priv y F/V como listas administrables.
- RN-022: el operativo carga el número de factura y pasa el ítem a Facturado.

## Cómo se prueba

- `backend/tests/test_items_facturacion.py`:
  - Un ítem vacío se guarda en Borrador con el mes actual (HU-060, criterios 1 y 2; HU-065,
    criterio 1).
  - El CUIT del ítem es independiente del cliente (HU-060, criterio 3).
  - Vínculo con una campaña.
  - Filtros.
  - Sin `DELETE`. Usuario de Lectura sin escritura.
  - Ítems no editables fuera de Borrador.
- `backend/tests/test_importes_facturacion.py` (`@pytest.mark.regla("RN-023")` donde aplique):
  - 10 × 1000 al 21 % da 10000, 2100 y 12100 (HU-061, criterio 1).
  - Neto a mano respetado (criterio 2). Solo neto (criterio 3).
  - Cambio de alícuota (criterio 4).
  - Redondeo al centavo con `Decimal`.
  - IVA y total no escribibles.
  - Totales del mes sin los anulados (HU-065, criterio 3).
- `backend/tests/test_estados_facturacion.py`:
  - Transiciones válidas e inválidas.
  - Facturado sin número rechazado (HU-065, criterio 2).
  - Auditoría con el usuario.
- Frontend:
  - `ItemsPage.test.tsx`: listado por mes con totales, anulados sin sumar, anular y marcar
    facturado.
  - `ItemForm.test.tsx`: precarga de CUIT y de campaña sin pisar lo escrito, y neto sugerido.

## Registro de gates

- Gate 1 (plan): 2026-10-27 — aprobado por Gonza
- Gate 2 (verificación): 2026-10-27 — `ruff format --check` (127 archivos) y `ruff check`
  sin errores; `mypy backend` sin errores (127 archivos); `makemigrations --check` sin cambios;
  `pytest --cov`: 634 tests en verde, coverage 96,56 %; frontend `format:check`, `lint`,
  `typecheck` y `build` en verde, `test:coverage` con 278 tests en verde y 92,91 % de líneas
  (90,34 % de sentencias); `pre-commit run --all-files` en verde.
  Espera revisión de Gonza o Juan Diego.
- Gate 3 (PR): pedido por Gonza el 2026-10-27
