# Unidad: Cierre de mes

- **Estado:** en curso · **Épica:** E11 Facturación mensual · **App dueña:** `facturacion`
- **Origen:** HU-066 (RN-022, RN-024, RN-025) · **Rama:** `feature/facturacion-cierre-de-mes`

## Objetivo

"Enviar a facturar" toma los ítems del mes que están en Borrador y completos, los pasa a Enviado a
facturar y genera la planilla .xlsx para Administración. Los incompletos se listan con lo que les
falta. Cada envío queda registrado: quién lo hizo, cuándo y qué ítems incluyó. Es la segunda
unidad de E11 para la entrega del viernes 30/10. La rama sale de la de
[items-a-facturar](items-a-facturar.md), porque necesita su modelo.

## Decisiones

1. **Qué se envía** (RN-025, provisoria): los ítems del mes en Borrador que tienen cliente,
   importe neto y mes. Los incompletos no se envían y se informan con lo que les falta
   (criterio 4). Los Anulados, los Facturados y los ya Enviados no entran (criterio 5). Si no hay
   ningún ítem completo, no se crea un envío vacío.
2. **El envío es un registro propio** (criterio 6): `EnvioFacturacion` guarda el mes, el usuario,
   la fecha y hora, y los ítems incluidos. Todo ocurre en una transacción: se bloquean los ítems
   del mes (`select_for_update`), se pasan a Enviado y se crea el envío. Dos envíos simultáneos
   del mismo mes no pueden mandar un ítem dos veces. El cambio de estado de cada ítem queda
   auditado.
3. **La planilla se genera en el servidor con `openpyxl`** (propuesta, [ADR-0008](../../adr/0008-planilla-xlsx-con-openpyxl.md)):
   - Es una dependencia nueva del backend.
   - Se genera a partir del envío guardado, así que la planilla siempre coincide con lo
     registrado.
   - Se puede volver a descargar después, desde `GET /api/facturacion/envios/<id>/planilla/`.
   - Se descartó generarla en el navegador porque haría falta una librería de frontend más
     pesada y la planilla quedaría desacoplada del registro del envío.
4. **Columnas** (RN-024, provisoria, **a validar con la planilla real de Seba**):
   - Mes, Cliente, CUIT, Marca, Descripción, Período desde, Período hasta, Cantidad, Precio
     unitario, Importe neto, Alícuota IVA, IVA, Total, Tipo de servicio, Tipo de soporte,
     Gob/Priv, Tipo de venta y Notas.
   - Al final van las nuevas: Orden de compra y Grupo de factura. Quedan vacías hasta HU-062 y
     HU-064 (entrega del 04/11).
   - Los importes van como números, no como texto, para que Administración pueda sumarlos.
   - Las filas se ordenan por cliente. "Ítems agrupados" (criterio 3) es HU-064, que queda para
     el 04/11.
   - Las columnas están definidas en una sola lista del servicio: cuando llegue la planilla real,
     ajustarlas es un cambio de una línea por columna.
5. **Costos y neto final** (criterio 1): el listado del mes ya muestra el neto. Los costos del
   ítem y el neto final son HU-063, que va en la entrega del 04/11. Hasta entonces, los totales
   del mes muestran solo neto, IVA y total, y el plan de HU-063 suma las columnas de costos.
6. **Quién envía** (RN-022, provisoria): el operativo. Administración recibe la planilla por
   fuera del sistema (la descarga quien envía). El aviso por correo es HU-067, para el 04/11.

## Cambios

- `pyproject.toml` del backend: `openpyxl` como dependencia.
- `docs/adr/0008-planilla-xlsx-con-openpyxl.md`: el ADR de la planilla.
- `facturacion/models.py`: `EnvioFacturacion` con `mes`, `enviado_por`, `enviado_en` y una
  relación muchos a muchos con `ItemFacturacion`.
- `facturacion/services.py`:
  - `faltantes_para_enviar(item)`.
  - `enviar_a_facturar(mes, usuario)` devuelve el envío y los incompletos.
  - `planilla_xlsx(envio)` arma el archivo con las columnas de la decisión 4.
- `facturacion/views.py` y `urls.py`:
  - `POST /api/facturacion/envios/` con `{mes: "AAAA-MM"}` devuelve el envío y los incompletos
    con sus faltantes.
  - `GET /api/facturacion/envios/?mes=` lista los envíos del mes.
  - `GET /api/facturacion/envios/<id>/planilla/` descarga el .xlsx.
  - Los permisos son los de los ítems: el operativo envía y Lectura ve y descarga.
- Frontend, en `ItemsPage`:
  - Un botón "Enviar a facturar" para el mes, visible si hay ítems en Borrador.
  - El resumen de enviados e incompletos con lo que les falta.
  - Un enlace para descargar la planilla.
  - Una sección "Envíos del mes" con quién envió, cuándo, cuántos ítems y la descarga.

## Migraciones

Una nueva en `facturacion`: crea `EnvioFacturacion` y su relación con los ítems. No mueve datos.

## Reglas provisorias que se usan

- RN-022: el operativo envía y Administración recibe la planilla.
- RN-024: las columnas propuestas en la decisión 4 hasta tener la planilla real.
- RN-025: se envían los completos y los incompletos se listan con lo que les falta.

## Cómo se prueba

- `backend/tests/test_cierre_de_mes.py`:
  - Los completos pasan a Enviado, y el envío registra usuario, fecha e ítems (criterios 2 y 6).
  - Los incompletos quedan en Borrador y se informan con sus faltantes (criterio 4,
    `@pytest.mark.regla("RN-025")`).
  - Anulados, Facturados, ya Enviados y de otros meses no entran (criterio 5).
  - Un mes sin completos no crea un envío.
  - Los cambios de estado quedan auditados.
  - Pedido inválido: 400. Usuario de Lectura: 403 al enviar.
  - Concurrencia: dos envíos simultáneos del mismo mes no duplican ítems (hilos sobre
    PostgreSQL).
- `backend/tests/test_planilla_facturacion.py`, que lee el .xlsx generado con `openpyxl`:
  - Tiene las columnas en orden, con Orden de compra y Grupo de factura al final (criterio 3,
    `@pytest.mark.regla("RN-024")`).
  - Los importes son numéricos y las filas están ordenadas por cliente.
  - Solo aparecen los ítems del envío (criterio 5).
  - La descarga tiene el tipo de contenido y el nombre de archivo correctos.
- Frontend `ItemsPage.test.tsx`:
  - Enviar a facturar con el resumen de incompletos.
  - Descarga de la planilla.
  - Envíos del mes.
  - El botón se oculta sin Borradores y para Lectura.

## Registro de gates

- Gate 1 (plan): 2026-10-27 — aprobado por Gonza
- Gate 2 (verificación): 2026-10-27 — `ruff format --check` (129 archivos) y `ruff check`
  sin errores; `mypy backend` sin errores (129 archivos); `makemigrations --check` sin cambios;
  `pytest --cov`: 651 tests en verde (incluida la concurrencia de dos envíos), coverage 96,66 %;
  frontend `format:check`, `lint`, `typecheck` y `build` en verde, `test:coverage` con 284 tests
  en verde y 93,03 % de líneas (90,46 % de sentencias); `pre-commit run --all-files` en verde.
  Espera revisión de Gonza o Juan Diego.
- Gate 3 (PR): pendiente
