# Unidad: Orden de compra y grupos de factura

- **Estado:** mergeada · **Épica:** E11 Facturación mensual · **App dueña:** `facturacion`
- **Origen:** HU-062, HU-064 (RN-024) · **Rama:** `feature/facturacion-orden-de-compra-y-grupos`

## Objetivo

El ítem guarda su orden de compra (número, fecha de aprobación y PDF) y puede agruparse con otros
en una misma factura. La planilla llena las columnas Orden de compra y Grupo de factura, que hoy
salen vacías, y muestra juntos los ítems de un grupo (HU-066, criterio 3). Es la primera de las
tres unidades del Should de E11 para el miércoles 04/11.

## Decisiones

1. **El PDF se guarda en PostgreSQL** (decisión de Gonza del 27/10/2026, [ADR-0009](../../adr/0009-pdf-de-orden-de-compra-en-postgresql.md)):
   - En Render el disco se borra en cada deploy y no hay almacenamiento de archivos.
   - El PDF va en un modelo aparte, `OrdenCompraPdf` (binario, nombre y tamaño), uno por ítem,
     para no cargar el binario cada vez que se listan ítems.
   - Se acepta solo PDF: extensión `.pdf` y contenido que empieza con `%PDF-` (criterio 3).
   - Tamaño máximo de 5 MB, configurable con la variable `FACTURACION_OC_MAX_MB`.
   - Se descartaron el disco persistente de Render (pago, no sirve en staging) y un bucket S3/R2
     (dependencia, credenciales y una cuenta más para el traspaso).
2. **Orden de compra en el ítem** (HU-062): `orden_compra_numero` y `orden_compra_fecha`,
   opcionales (criterio 4). Se editan solo en Borrador, como el resto de los datos.
3. **Duplicado de OC** (criterio 2): al guardar, la respuesta trae `avisos.orden_compra` con los
   ítems no anulados que tienen el mismo número. No bloquea. Al guardar, la página muestra el
   aviso con el número y la descripción de cada ítem coincidente (sin enlace: puede ser de otro
   mes). El número se compara sin espacios al principio ni al final y sin distinguir mayúsculas.
4. **Grupo de factura** (HU-064): un modelo `GrupoFactura` (mes, creado por, creado en) y un
   `grupo` opcional en el ítem.
   - Agrupar: se eligen ítems del listado y se usa "Agrupar en una factura". Si alguno ya tiene
     grupo, los demás se suman a ese; si hay dos grupos distintos, se rechaza.
   - Todos los ítems de un grupo son del mismo mes y están en Borrador.
   - Quitar del grupo deja el ítem independiente (criterio 2). Un grupo sin ítems queda vacío y
     no aparece en ningún lado.
   - El identificador visible es `G-<id>`.
   - Agrupar y quitar quedan auditados como un cambio del campo `grupo`.
5. **CUIT distinto del cliente** (criterio 4 de HU-064): ya funciona desde HU-060. Se agrega el
   test que lo cubre en la planilla.
6. **Planilla** (RN-024, provisoria): Orden de compra muestra el número (y la fecha, en una
   columna nueva "Fecha OC" al final). Grupo de factura muestra `G-<id>`. Las filas se ordenan
   por cliente y, dentro del cliente, los ítems de un grupo quedan juntos.

## Cambios

- `facturacion/models.py`: `GrupoFactura`, `OrdenCompraPdf`, y en el ítem
  `orden_compra_numero`, `orden_compra_fecha` y `grupo`.
- `facturacion/services.py`:
  - `ordenes_de_compra_duplicadas(item)`.
  - `agrupar(items, usuario)` y `quitar_del_grupo(item, usuario)`.
  - `validar_pdf(archivo)`.
  - `COLUMNAS_PLANILLA` y el orden de `planilla_xlsx`.
- `facturacion/views.py`, `serializers.py` y `urls.py`:
  - El ítem expone los campos de OC, `tiene_pdf`, `grupo` y `avisos`.
  - `PUT`, `GET` y `DELETE /api/facturacion/items/<id>/orden-compra-pdf/` (multipart al subir;
    `GET` devuelve el PDF para abrirlo en el navegador). Quitar el PDF es reemplazar un adjunto,
    no borrar un ítem.
  - `POST /api/facturacion/grupos/` con `{items: [...]}` y
    `POST /api/facturacion/items/<id>/quitar-del-grupo/`.
  - Permisos: los de los ítems (el operativo edita, Lectura ve y abre el PDF).
- `config/settings.py` y `backend/.env.example`: `FACTURACION_OC_MAX_MB`.
- `docs/manual/manual-de-uso.md`: orden de compra y grupos de factura.
- `docs/adr/0009-pdf-de-orden-de-compra-en-postgresql.md`.
- Frontend:
  - `ItemForm`: número y fecha de la OC, y `PdfOrdenCompra` para adjuntar, abrir y quitar el
    PDF. El PDF se adjunta a un ítem ya guardado; en uno nuevo se pide guardarlo primero.
  - `ItemsPage`: el aviso de OC duplicada después de guardar, y la OC con el enlace al PDF en la
    fila.
  - `ItemsPage`: selección de ítems en Borrador, "Agrupar en una factura", columna Grupo y
    "Quitar del grupo".

## Migraciones

Una nueva en `facturacion`: crea `GrupoFactura` y `OrdenCompraPdf` y agrega tres campos opcionales
al ítem. No mueve datos.

## Reglas provisorias que se usan

- RN-024: las columnas nuevas siguen al final, y se suma "Fecha OC".

## Cómo se prueba

- `backend/tests/test_orden_de_compra.py`:
  - Número, fecha y PDF quedan guardados y el PDF se abre (criterio 1).
  - Un número repetido avisa con el ítem coincidente y guarda igual; un ítem anulado no cuenta
    (criterio 2).
  - Un archivo que no es PDF, o que supera el tamaño máximo, se rechaza con mensaje (criterio 3).
  - Un ítem sin OC se guarda (criterio 4).
  - Fuera de Borrador no se edita la OC. Lectura no sube PDF (403).
- `backend/tests/test_grupos_factura.py`:
  - Tres ítems agrupados comparten el grupo (criterio 1); quitar uno lo deja independiente
    (criterio 2).
  - Se rechazan ítems de otro mes, fuera de Borrador o de dos grupos distintos.
  - Agrupar y quitar quedan auditados.
- `backend/tests/test_planilla_facturacion.py`: columnas con OC, fecha y grupo
  (`@pytest.mark.regla("RN-024")`); los ítems de un grupo salen juntos (criterio 3 de HU-064 y
  de HU-066); el CUIT del ítem distinto del cliente sale en la planilla (criterio 4).
- Frontend: `ItemForm.test.tsx` (OC, PDF, aviso de duplicado y errores de archivo) e
  `ItemsPage.test.tsx` (agrupar, columna de grupo, quitar del grupo, oculto para Lectura).

## Registro de gates

- Gate 1 (plan): 2026-10-27 — aprobado por Gonza
- Gate 2 (verificación): 2026-10-27 — `ruff format --check` (133 archivos) y `ruff check` sin
  errores; `mypy backend` sin errores (133 archivos); `makemigrations --check` sin cambios;
  `pytest --cov`: 710 tests en verde, coverage 96,79 %; frontend `format:check`, `lint`,
  `typecheck` y `build` en verde, `test:coverage` con 311 tests en verde y 93,4 % de líneas
  (90,9 % de sentencias); `pre-commit run --all-files` en verde. Espera revisión de Gonza o Juan
  Diego. Aprobado por Gonza el 2026-10-27.
- Gate 3 (PR): #81, pedido por Gonza el 2026-10-27
