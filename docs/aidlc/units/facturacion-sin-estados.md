# Unidad: facturacion-sin-estados

- **Estado:** en curso · **Épica:** E11 Facturación mensual · **App dueña:** `facturacion`
- **Origen:** pedido de Juan Diego (2026-11-16): HU-065, HU-066 y HU-067 retiradas, HU-060 y HU-064
  ajustadas en el PR de historias `docs/historias-facturacion-sin-estados` ·
  **Rama:** `feature/facturacion-sin-estados`

## Objetivo

Facturación deja de tener «Enviar a facturar» y estados. El ítem se carga, se edita cuando haga
falta y se baja en Excel. Si se cargó por error, se da de baja sin borrarse (baja lógica,
`CLAUDE.md` §5).

## Decisión de diseño

El modelo no cambia y no hay migración. El campo `estado` queda solo para la baja lógica:
`anulado` es «dado de baja» y los demás valores cuentan como ítem vigente. Los ítems que hoy están
Enviados o Facturados en producción pasan a editarse como cualquier otro, y conservan su número de
factura y su historial en la base. Los modelos `EnvioFacturacion` y los campos de reapertura y
anulación quedan en la base, sin uso desde la app, para no perder lo ya registrado.

## Cambios

### Backend (`apps/facturacion`)

- `services.py`:
  - Se borran `TRANSICIONES_ITEM`, `CAMPOS_FUERA_DE_BORRADOR`, `validar_cambio_de_item` y sus
    ayudantes; `enviar_a_facturar`, `faltantes_para_enviar` y lo del reenvío; `planilla_xlsx`,
    `COLUMNAS_PLANILLA`, `TITULOS_ANTERIORES` y `valores_de_planilla`; `reabrir_item`,
    `anular_facturado` y `avisar_a_administracion`.
  - `_exigir_borrador` pasa a `_exigir_vigente`: costos, orden de compra y grupo de factura se
    pueden cambiar en cualquier ítem que no esté dado de baja.
  - `_mes_agrupable`: se agrupan ítems vigentes, no solo los Borradores.
  - `dar_de_baja(item, usuario)`: nuevo. Pasa el ítem a `anulado`, con fecha y usuario, auditado
    (HU-007) en la misma transacción.
- `views.py`:
  - Se borran `EnvioFacturacionViewSet` y su ruta `envios`, y las acciones `reabrir` y
    `anular-facturado`.
  - Nueva acción `POST items/<id>/dar-de-baja/`.
  - La lista, los totales y el Excel excluyen siempre los dados de baja; el filtro `estado` se
    saca. Un ítem dado de baja no se puede editar (404 en el `PATCH`).
- `serializers.py`: `estado`, `numero_factura` y los campos de reapertura y anulación salen de la
  API (si llegan en un pedido, se ignoran). Se borra `EnvioFacturacionSerializer`.
- `admin.py`: sin cambios (el admin puede seguir viendo el estado guardado).
- `config/settings.py`, `backend/.env.example` y `render.yaml`: se saca
  `FACTURACION_CORREO_ADMINISTRACION`, que solo usaban los avisos. `EMAIL_*` queda configurado,
  pero hoy ninguna funcionalidad manda correos (el plan decía que lo usaban otras partes: no es
  así). Sacarlo queda para otra unidad.

### Frontend (`features/facturacion`)

- Se borran `EnviosDelMes.tsx` y su test: el recuadro «Envíos a facturar» desaparece.
- `ItemsPage.tsx`:
  - Sin filtro de estado.
  - En el menú de la fila: **Editar** y **Dar de baja** en todos los ítems; se van **Marcar
    facturado**, **Reabrir** y **Anular** con motivo, junto con el campo de texto que pedían.
  - La casilla para agrupar aparece en todos los ítems.
  - La cifra «Ítems» deja de decir «sin anulados».
- `types.ts`: se van `EstadoItem`, `ESTADOS_ITEM`, `etiquetaEstadoItem` y los tipos del envío.
- `CostosDelItem.tsx` y `PdfOrdenCompra.tsx`: sin cambios. El servidor sigue respondiendo con el
  campo `estado` cuando el ítem está dado de baja, así que sus mensajes de error siguen sirviendo.

### Documentación

- `docs/aidlc/reglas-de-negocio.md`: "Dónde vive" de RN-022, RN-024, RN-025 y RN-026.
- `docs/manual/manual-de-uso.md`: Facturación sin estados, envío ni reapertura, con «Dar de baja»
  y con el formato nuevo del Excel.
- `docs/manual/guion-de-capacitacion.md`: el bloque de Facturación y las preguntas RN-022, RN-025
  y RN-026, que ya no aplican.
- `docs/operacion/traspaso-de-accesos.md`: el correo para avisos pasa a «no aplica».

## Fuera de alcance

- Borrar de la base los campos y la tabla de envíos: se puede hacer más adelante con una
  migración, cuando se confirme que nadie extraña ese historial.
- El formato del Excel: va en la unidad `facturacion-planilla-con-formato`.

## Migraciones

Ninguna. `makemigrations --check` tiene que seguir sin cambios.

## Reglas provisorias que se usan

- RN-024 (`provisoria`): el Excel de la lista no cambia de columnas.
- RN-022, RN-025 y RN-026 quedan sin efecto: su código se borra.

## Cómo se prueba

- Primero los tests nuevos, en rojo: `backend/tests/test_baja_item_facturacion.py`:
  - `test_dar_de_baja_item_lo_saca_de_la_lista_los_totales_y_el_excel`
  - `test_dar_de_baja_queda_auditado_con_usuario_y_fecha`
  - `test_item_dado_de_baja_no_se_edita`
  - `test_item_enviado_o_facturado_se_edita_como_cualquiera` (ítems que ya están así en la base)
  - `test_lectura_no_puede_dar_de_baja`
  - `test_no_hay_endpoint_de_envios_ni_reabrir_ni_anular_facturado` (404)
- Se borran los tests de lo retirado: `test_cierre_de_mes.py`, `test_reabrir_item.py`,
  `test_anular_facturados.py`, `test_planilla_facturacion.py` y `test_estados_facturacion.py`. Se
  ajustan los que exigían Borrador (`test_grupos_factura.py`, costos y orden de compra) para que
  exijan «vigente».
- Frontend: `ItemsPage.test.tsx` sin envío, filtro ni estados, y con «Dar de baja».
- Verificación completa de backend y frontend, `makemigrations --check` y `pre-commit`.
- Prueba visual en local: la pantalla Facturación sin el recuadro y con «Dar de baja».

## Registro de gates

- Gate 1 (plan): 2026-11-16 — aprobado por Juan Diego
- Gate 2 (verificación): 2026-11-16 — aprobado por Juan Diego. Salida de los comandos:
  - `test_baja_item_facturacion.py` fallaba antes del cambio (`12 failed, 1 passed`) y pasa después
    (`13 passed`); en el frontend, 16 tests de `ItemsPage` fallaban antes y pasan después.
  - Se borraron 5 archivos de tests de lo retirado y se ajustaron 14 tests a «dado de baja».
  - `ruff format --check` (`144 files already formatted`), `ruff check` (`All checks passed!`),
    `mypy backend` (`Success: no issues found in 144 source files`) y `makemigrations --check`
    (`No changes detected`).
  - `pytest --cov`: `890 passed in 1064.85s`, coverage total 97,29 %, ningún test salteado.
  - Frontend: `format:check` (`All matched files use Prettier code style!`), `lint` y `typecheck`
    sin errores, `test:coverage` con `394 passed` en 50 archivos (sentencias 92,72 %, líneas
    94,70 %), `build` `✓ built in 1.88s`.
  - `pre-commit run --all-files`: todos `Passed`, incluido gitleaks.
- Gate 3 (PR): pendiente
