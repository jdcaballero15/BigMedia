# Unidad: anular-facturados

- **Estado:** en revisión · **Épica:** E11 Facturación mensual · **App dueña:** facturacion
- **Origen:** RN-026, HU-067 (criterios 5 y 6) · **Rama:** `feature/facturacion-anular-facturados`
- **Depende de:** [`reabrir-item`](reabrir-item.md) (aviso a Administración y auditoría) y el PR #99
  (RN-026 en `provisoria`), que tiene que estar mergeado antes del PR de código.

## Objetivo

Que un ítem Facturado se pueda anular cuando hay que corregirlo, con motivo, auditado y con aviso a
Administración, para que no quede contado en el resumen del mes. La corrección se carga como un
ítem nuevo, con lo que ya existe.

## Encuadre

- **RN-026 (`provisoria`, 2026-10-28):** un Facturado no se reabre ni se edita. Se anula con motivo
  obligatorio, queda auditado con su número de factura, sale del resumen del mes y de la planilla, y
  Administración recibe un aviso. Los reportes de ingresos no cambian (salen de las reservas).
- **App dueña:** `facturacion`. Usa `auditoria` por su servicio, como la reapertura. Sin
  dependencias nuevas entre apps.
- **Capas:** backend (`facturacion`: modelo, servicio, vista) y frontend (`features/facturacion`).

## Cambios

- **Modelo `ItemFacturacion`:** `anulado_en`, `anulado_por` y `motivo_anulacion`, no editables,
  igual que los de la reapertura. Se llenan solo al anular un Facturado.
- **Servicio `anular_facturado(item_id, motivo, usuario)`** en `apps/facturacion/services.py`, con el
  mismo esquema que `reabrir`:
  - motivo obligatorio (recortado a 200 caracteres); si falta, error en `motivo`;
  - `transaction.atomic()` y `select_for_update()`; solo para un ítem Facturado, si no, error en
    `estado`;
  - pasa a Anulado, **conserva `numero_factura`** y guarda quién, cuándo y por qué;
  - auditoría de `estado` y `motivo_anulacion` en la misma transacción;
  - aviso a Administración al confirmarse la transacción (`transaction.on_commit`), con el ítem,
    el mes, el número de factura, quién lo anuló, el motivo, y que la corrección llega como un ítem
    nuevo.
- **Vista:** acción `POST /api/facturacion/items/<id>/anular-facturado/` con `{ "motivo" }`, igual
  que `reabrir`. El `PATCH` con `estado: anulado` sigue como hoy para Borrador y Enviado; para un
  Facturado sigue rechazado (la transición `FACTURADO → ANULADO` no se agrega a
  `TRANSICIONES_ITEM`: solo se llega por la acción con motivo).
- **Serializer:** `motivo_anulacion`, `anulado_en` y `anulado_por_nombre`, de solo lectura.
- **Frontend (`ItemsPage`):** en un ítem Facturado, acción «Anular» que pide el motivo (como
  «Reabrir») y llama a la acción nueva. En un ítem anulado con motivo, el motivo se ve en la fila.
- **Grupos de factura (propuesta):** se anula de a un ítem, aunque esté en un grupo; el aviso
  dice el código del grupo para que Administración revise la factura completa.
- **Docs:** columna «Dónde vive» de RN-026 y el manual de uso (Después del envío).

## Fuera de alcance

- Generar el ítem de corrección automáticamente (se carga a mano, como cualquier ítem).
- Registrar el número de la nota de crédito (va en el motivo si hace falta).
- Cambios en los reportes de ingresos.

## Migraciones

`facturacion.00xx_anulacion_de_facturado`: agrega tres columnas que aceptan vacío. Aditiva, sin
mover datos.

## Reglas provisorias que se usan

- RN-026: anular con motivo, auditado y con aviso; la corrección va en un ítem nuevo.
- RN-022: el aviso a Administración sale por correo (o queda en el log si no hay dirección).

## Cómo se prueba

- Backend, en un archivo nuevo `backend/tests/test_anular_facturados.py`, con
  `@pytest.mark.regla("RN-026")`:
  - `test_anular_facturado_con_motivo_lo_anula_y_conserva_el_numero`;
  - `test_anular_facturado_sin_motivo_se_rechaza`;
  - `test_anular_facturado_un_item_que_no_esta_facturado_se_rechaza`;
  - `test_anular_facturado_queda_auditado`;
  - `test_anular_facturado_avisa_a_administracion_al_confirmar`;
  - `test_anular_facturado_lo_saca_de_los_totales_del_mes`;
  - `test_patch_a_anulado_de_un_facturado_sigue_rechazado`;
  - `test_lectura_no_puede_anular_un_facturado`.
- Frontend: la acción pide el motivo y llama al endpoint; un anulado muestra su motivo.
- Revisión visual con Gonza en el navegador.
- Definition of Done completa.

## Registro de gates

- Gate 1 (plan): aprobado por Gonza el 2026-10-28, con la propuesta de anular de a un ítem aunque esté en un grupo.
- Gate 2 (verificación): 2026-10-28, ruff, mypy, makemigrations y pre-commit (gitleaks) limpios; pytest 812 passed, 96,95 %; frontend format, lint, typecheck, 372 tests (92,42 % sentencias, 94,45 % líneas) y build en verde. Revisión visual aprobada por Gonza el 2026-10-28. Rebaseada sobre develop con el PR #99 y columna «Dónde vive» de RN-026 completada.
- Gate 3 (PR): #100, abierto el 2026-10-28 a pedido de Gonza.
