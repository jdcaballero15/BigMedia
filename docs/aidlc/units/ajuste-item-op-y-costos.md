# Unidad: Orden de publicidad y costos elegidos en el ítem a facturar

- **Estado:** en curso · **Épica:** E11 Facturación mensual · **App dueña:** `facturacion`
- **Origen:** pedido de Juan Diego (2026-11-18); HU-060, HU-062, HU-063 ajustadas en
  `docs/historias-item-con-op-y-costos` · **Rama:** `feature/facturacion-item-op-y-costos`
- **Depende de:** el merge del PR `docs/historias-item-con-op-y-costos`.

## Objetivo

En el formulario del ítem de Facturación se adjunta ahí mismo la orden de publicidad (PDF) y se
eligen varios costos ya cargados (por ejemplo impresión y fijación). Si el ítem tiene costos
elegidos, «Costos incluidos» es su suma y «Detalle costo» sus tipos, calculados solos.

## Decisiones (respuestas de Juan Diego del 2026-11-18)

1. **Orden de publicidad = el PDF del ítem de HU-062.** No hay modelo nuevo: se reusa
   `OrdenCompraPdf` (en la base, ADR-0009) y en pantalla se llama «Orden de publicidad». Uno por
   ítem; adjuntar otro lo reemplaza. No se vincula con las OP de la campaña (HU-069).
2. **Costos de cualquier campaña.** Se puede elegir cualquier costo no anulado que no esté en otro
   ítem activo, con buscador por campaña, cartel, tipo o destinatario. Deja de exigirse que sea de
   la campaña del ítem (hoy `vincular_costo` lo exige).
3. **Costos incluidos y detalle calculados.** Con costos elegidos: suma de montos no anulados y
   tipos sin repetir unidos por « + ». Se calculan **al leer** (serializer, lista, totales y
   Excel), no se guardan: así un costo anulado o editado en `costos` (que no puede importar de
   `facturacion`) se refleja sin sincronizar nada. Los valores escritos a mano quedan guardados en
   el ítem y vuelven a valer si se quitan todos los costos elegidos.
4. **Una sola acción de guardar.** El alta y la edición del ítem aceptan `multipart/form-data`
   con el PDF opcional (`orden_publicidad`) y la lista de costos elegidos (`costos`), y todo se
   guarda en una transacción: si el PDF se rechaza, el ítem no se guarda a medias y el formulario
   conserva lo cargado (como HU-069). Así funciona también en Nuevo ítem, sin «guardá primero».
5. **Quitar un costo sin DELETE** (baja lógica). `CostoDeItem` pasa de `OneToOneField` a
   `ForeignKey` con `quitado_en` y `quitado_por`, y una restricción única parcial: un costo está en
   un solo ítem a la vez entre los vínculos sin quitar. Quitar se audita (HU-007), igual que hoy
   vincular. Los costos propios del ítem (sin reserva, HU-063) no se quitan: se anulan como hoy.
6. **Totales del mes sin cambio.** «Costos» ya suma los costos del módulo vinculados al ítem; los
   costos incluidos escritos a mano siguen sin entrar ahí, como hoy. El Excel toma el valor
   calculado en su columna y sus fórmulas de totales no cambian (RN-024).

## Cambios

- `facturacion/models.py`: `CostoDeItem` con FK, `quitado_en`, `quitado_por` y la restricción
  única parcial.
- `facturacion/services.py`:
  - `costos_elegibles(busqueda)`: costos no anulados sin vínculo activo, con reserva, campaña y
    cartel.
  - `guardar_item(...)`: crea o edita el ítem, reemplaza el PDF si viene y deja como elegidos
    exactamente los `costos` pedidos (vincula los nuevos, quita los que faltan), todo en
    `transaction.atomic()` con `select_for_update()` sobre los costos.
  - `costos_incluidos_del_item(item)` y `detalle_costo_del_item(item)`: valor calculado o el
    escrito a mano. Los usan el serializer y `COLUMNAS_DESCARGA`.
  - `costos_vinculables` y `vincular_costo` dejan de filtrar por la campaña del ítem.
- `facturacion/serializers.py` y `views.py`: el ítem expone `costos_calculados` (bool), los
  costos elegidos (id, tipo, monto, campaña, cartel, destinatario) y `orden_compra_pdf`; ignora
  `costos_incluidos` y `detalle_costo` escritos si hay costos elegidos. `GET
  /api/facturacion/costos-elegibles/?q=` para el buscador. Create y update aceptan multipart.
- Frontend (`features/facturacion/`):
  - `ItemForm`: debajo de los siete datos, la sección «Orden de publicidad» (adjuntar,
    reemplazar, abrir) y «Costos del ítem» (buscador, elegidos con su monto, quitar y la suma).
    Con costos elegidos, «Costos incluidos» y «Detalle costo» se muestran calculados y sin
    editar.
  - `ItemsPage`: el menú de la fila dice «Abrir orden de publicidad».
  - Se reusan y adaptan `PdfOrdenCompra` y `CostosDelItem`, que hoy no están montados.

## Migraciones

Una, en `facturacion`: `CostoDeItem.costo` de `OneToOneField` a `ForeignKey`, campos
`quitado_en` y `quitado_por` (nulos) y la restricción única parcial. No mueve datos: los vínculos
actuales quedan activos.

## Reglas provisorias que se usan

- RN-024: columnas de la planilla, sin cambio de valor.

## Cómo se prueba

- `backend/tests/test_item_op_y_costos.py`:
  - `test_costos_incluidos_con_impresion_y_fijacion_suma_y_arma_detalle` (HU-060 criterio 11):
    50000 + 30000 = 80000 y «Impresión + Fijación», en la API y en el Excel.
  - `test_costos_incluidos_sin_costos_elegidos_usa_lo_escrito` (criterios 9 y 12).
  - `test_costos_elegibles_de_otra_campania_aparecen` y
    `test_costos_elegibles_anulado_o_en_otro_item_no_aparece` (HU-063 criterios 6 y 7).
  - `test_quitar_costo_lo_libera_sin_anularlo_y_audita` (criterio 8).
  - `test_costo_anulado_en_modulo_deja_de_sumar` (criterio 9).
  - `test_guardar_item_con_pdf_invalido_no_guarda_nada` y
    `test_guardar_item_nuevo_con_pdf_y_costos` (HU-062 criterio 5, decisión 4).
  - Concurrencia: dos ítems que eligen el mismo costo a la vez, solo uno lo obtiene.
- Se ajustan los tests de `test_costos_del_item.py` que exigían la campaña del ítem.
- Frontend: `ItemForm.test.tsx` (secciones, campos calculados de solo lectura, envío
  multipart, error de PDF conserva lo cargado), `CostosDelItem.test.tsx` (buscar, elegir, quitar,
  suma) e `ItemsPage.test.tsx` (texto del menú).

## Registro de gates

- Gate 1 (plan): pendiente
- Gate 2 (verificación): pendiente
- Gate 3 (PR): pendiente
