# Unidad: Campaña siempre confirmada

- **Estado:** en revisión · **Épica:** E10 Armado de campañas y reserva masiva · **Apps:** `reservas`,
  `campanias`, frontend
- **Origen:** PR de historias #142 (HU-024, HU-035, HU-037, HU-057, HU-058, HU-071; HU-059
  retirada; RN-002, RN-006, RN-011) · **Rama:** `feature/reservas-campania-siempre-confirmada`

## Objetivo

Seba solo maneja el estado de la campaña. La campaña nace Confirmada y solo puede pasar a
Cancelada. Sus reservas nacen Confirmadas y su estado lo lleva el sistema. Desaparecen Cotizada,
Perdida, Pendiente, "Confirmar reservas" y las tentativas.

## Decisiones

Las decisiones de negocio están en #142 (Juan Diego, 17/11/2026). Las técnicas son propuestas:

1. **Cancelar la campaña es una acción de `reservas`.** `campanias` no puede importar `reservas`
   (CLAUDE.md, sección 2), y cancelar tiene que tocar las reservas en la misma transacción. Por
   eso se crea `POST /api/reservas/reservas/cancelar-campania/` con el servicio
   `cancelar_campania(campania, usuario)`. Ese servicio pasa la campaña a Cancelada y en la misma
   transacción:
   - cancela las reservas que todavía no empezaron;
   - termina hoy las que están en exhibición;
   - deja como están las que ya terminaron.

   El `PATCH` de la campaña deja de aceptar `estado`. Se descartó una señal de Django porque
   esconde el efecto en otra app.
2. **Quitar una reserva:** `POST /api/reservas/reservas/{id}/quitar/`. Si todavía no empezó,
   queda Cancelada. Si está en exhibición, su `fecha_fin` pasa a hoy y sigue Confirmada. Si ya
   terminó o está Cancelada, se rechaza. Acortar nunca necesita validar cupo, porque solo libera
   días. Todo queda en auditoría.
3. **Las reservas nacen Confirmadas:**
   - El alta individual y la creación en bloque (`_crear_en_tanda`) validan el cupo con el cartel
     bloqueado (`conflictos_de`, HU-034).
   - En bloque, la que no entra va a `fallidas` con el motivo y con qué campaña lo ocupa.
   - El campo `estado` deja de ser editable en la API, tanto al crear como al editar.
   - Una campaña Cancelada no admite reservas nuevas.
4. **Finalizada se calcula por fecha, sin tarea programada** (HU-036): la API expone
   `estado_visible`, que es Finalizada si la reserva está Confirmada y su `fecha_fin < hoy`. El
   estado guardado no cambia, así que no hace falta una tarea programada. Las reservas que ya
   tienen Finalizada guardada siguen igual, y el cupo se cuenta igual que hoy.
5. **Campaña:**
   - `Estado` queda con `CONFIRMADA` (default) y `CANCELADA`.
   - Marca, cliente que factura y fechas se exigen al crear y al editar (`validar_confirmacion`
     pasa a correr siempre). Una campaña vieja incompleta se completa la próxima vez que se edite.
6. **Migración de datos:** las campañas Cotizadas y Perdidas pasan a Canceladas, y las reservas
   Pendientes pasan a Canceladas. Va en una migración de datos por app, con la de `reservas`
   dependiendo de la de `campanias`. Después se achican los `choices` (sin `PENDIENTE`,
   `COTIZADA` ni `PERDIDA`). La migración no tiene vuelta atrás de datos: el reverse no hace nada.
7. **Se borra `tentativa_bloquea`** del modelo, del serializer, de la pantalla Parámetros (que
   está fuera del menú) y de la auditoría de parámetros, en lugar de dejarlo sin uso.
   `_estados_que_bloquean` pasa a ser una constante: Confirmada y Finalizada.
8. **Se borra lo que queda sin uso:**
   - `confirmar_reservas_de_campania` y `confirmar-en-bloque`;
   - `mover_pendientes` y `mover-pendientes`, con `MoverPendientes.tsx`;
   - `validar_transicion` y `ESTADOS_INICIALES`;
   - en Posiciones, `tentativas` y `tentativas_detalle`.

## Cambios

- **`campanias`:**
  - `models.py`: estados y default.
  - `serializers.py`: `estado` de solo lectura y validación siempre.
  - `views.py`: quitar la auditoría de cambio de estado del `PATCH`.
  - Migraciones de datos y de `choices`.
- **`reservas`:**
  - `services.py`: `cancelar_campania`, `quitar_reserva`, alta y tanda Confirmadas con validación,
    `estado_visible`, borrar lo de la decisión 8 y simplificar `filtrar_vigentes`, `ESTADOS_*` y
    `necesita_validar_cupo`.
  - `serializers.py`, `views.py` y `urls.py`: acciones `quitar` y `cancelar-campania`, y borrar
    las acciones viejas.
  - `models.py`: borrar `PENDIENTE` y `tentativa_bloquea`.
  - Migraciones de datos y de esquema.
- **`usuarios`**: `_datos_demo.py` y `cargar_datos_ejemplo.py`, sin Cotizada, Perdida ni
  Pendiente.
- **Frontend:**
  - `campanias`:
    - `types.ts` y `CampaniaForm` (sin selector de estado);
    - `CampaniasLista` y `CampaniasPage` (filtro Confirmada/Cancelada);
    - `CampaniaDetalle`: botón "Cancelar campaña" con confirmación.
  - `reservas`:
    - `ReservaForm` sin estado;
    - `ReservasCampania`: sin "Confirmar reservas", con "Quitar" por fila y el estado visible;
    - `VistaPosiciones` y `AgregarCarteles` sin tentativas;
    - `ParametrosPage` sin el parámetro;
    - `types.ts`;
    - se borra `MoverPendientes.tsx`.
  - Los tests de cada componente se actualizan.
- **`docs/aidlc/reglas-de-negocio.md`:** columna "Dónde vive" de RN-002, RN-006 y RN-011.

## Migraciones

- `campanias`: datos (Cotizada y Perdida → Cancelada) y luego `AlterField` de `estado`.
- `reservas`: datos (Pendiente → Cancelada), `AlterField` de `estado` y `RemoveField` de
  `tentativa_bloquea`.
- Se revisan a mano y se comprueban con `makemigrations --check`.

## Reglas que se usan

- RN-006: cancelar la campaña y quitar, provisoria.
- RN-011: datos obligatorios al crear, provisoria.
- RN-001 y RN-003 siguen igual.
- RN-002 queda sin efecto.

## Cómo se prueba

- Backend:
  - `test_campania_nace_confirmada` (`regla("RN-011")`).
  - `test_crear_campania_sin_marca_cliente_o_fechas_rechaza` (`regla("RN-011")`).
  - `test_editar_estado_de_campania_por_patch_se_ignora_o_rechaza`.
  - `test_cancelar_campania_cancela_futuras_termina_en_curso_y_no_toca_terminadas`
    (`regla("RN-006")`).
  - `test_cancelar_campania_cancelada_rechaza`.
  - `test_quitar_reserva_futura_la_cancela` y `test_quitar_reserva_en_curso_la_termina_hoy`
    (`regla("RN-006")`).
  - `test_quitar_reserva_terminada_rechaza`.
  - `test_alta_individual_nace_confirmada_y_valida_cupo`.
  - `test_tanda_nace_confirmada_y_sin_cupo_va_a_fallidas`.
  - `test_tanda_dos_pedidos_al_ultimo_cupo_uno_falla` (concurrencia, HU-034).
  - `test_campania_cancelada_no_admite_reservas`.
  - `test_estado_de_reserva_no_se_edita`.
  - `test_estado_visible_finalizada_por_fecha`.
  - `test_migracion_pasa_cotizadas_perdidas_y_pendientes_a_canceladas`.
  - Se borran los tests de confirmación en bloque, de mover Pendientes, de transiciones y de
    tentativas.
- Frontend:
  - el formulario de campaña no tiene estado;
  - "Cancelar campaña" pide confirmación y llama al endpoint;
  - "Quitar" en una reserva;
  - la grilla y la tabla sin tentativas;
  - el formulario de reserva sin estado.
- Prueba manual en local:
  - crear una campaña;
  - agregar carteles y ver que quedan Confirmados;
  - agregar uno lleno y ver que falla;
  - quitar uno;
  - cancelar la campaña.

## Riesgos

- **La migración de datos no se puede deshacer.** Antes de mergear se revisa cuántas campañas
  Cotizadas o Perdidas y cuántas reservas Pendientes hay en producción.
- **Crear en bloque se vuelve más lento** porque cada cartel valida su cupo. El objetivo sigue
  siendo de 200 carteles en menos de un minuto, y la validación ya bloquea solo el cartel.

## Registro de gates

- Gate 1 (plan): 2026-11-18 — aprobado por Juan Diego
- Gate 2 (verificación): 2026-11-18 — rama `feature/reservas-campania-siempre-confirmada`:
  - `ruff format --check` y `ruff check`: All checks passed!
  - `mypy backend`: Success: no issues found in 144 source files
  - `makemigrations --check --dry-run`: No changes detected
  - `pytest --cov`: 873 passed in 1512.38s; Required test coverage of 80.0% reached. Total
    coverage: 97.42%
  - `pre-commit run --all-files` (incluye gitleaks): todos Passed
  - Frontend: `format:check` OK, `lint` OK, `typecheck` OK, `test:coverage` 50 archivos y 417
    tests passed (líneas 94,88 %), `build` OK
  - La primera corrida dio 869 passed y 4 errores de setup en tests transaccionales: el test
    nuevo de concurrencia usaba `transaction=True` sin `serialized_rollback=True` y dejaba la base
    vacía. Se corrigió y la segunda corrida es la de arriba.
  - Aprobado por Juan Diego el 2026-11-18, después de probarlo en local.
- Gate 3 (PR): 2026-11-18, pedido por Juan Diego
