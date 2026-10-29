# Unidad: cartel-fuera-de-servicio

- **Estado:** en curso · **Épica:** E5 Reservas y motor de disponibilidad · **App dueña:** reservas
- **Origen:** HU-039 (RN-010) · **Rama:** `feature/reservas-cartel-fuera-de-servicio`

## Objetivo

Que un cartel roto o apagado (estado no operativo) no se pueda reservar de nuevo hasta que vuelva a
un estado operativo, y que al pasarlo a ese estado el operativo vea qué reservas activas quedan
afectadas, para reubicarlas o avisar a los clientes.

## Encuadre

- **RN-010 (`provisoria`):** alertar y listar las reservas afectadas, sin modificarlas, y bloquear
  reservas nuevas sobre el cartel mientras no esté operativo.
- **Qué ya existe:** `EstadoCartel.operativo` y los cinco estados de `0002_catalogos_iniciales`
  (Activo es el único operativo; En mantenimiento, Apagado y Vidrio destruido no lo son; De baja
  tampoco). Hoy solo se bloquea el cartel **de baja** (`es_baja`), en el serializer de reserva y en
  la reserva masiva; los no operativos se pueden reservar.
- **App dueña:** `reservas`, que ya importa de `inventario`. El listado de reservas afectadas no
  puede vivir en `inventario` (no importa de `reservas`). Sin dependencias nuevas entre apps.
- **Capas:** backend (`reservas`: servicio, serializer, vista; `inventario`: un campo de solo
  lectura en el serializer de cartel) y frontend (`features/inventario` y `features/reservas`).

## Cambios

- **Servicio (`apps/reservas/services.py`):**
  - `validar_cartel_reservable(cartel)`: si el cartel no es operativo, `ValidationError` en
    `cartel`. Mensaje: «El cartel está de baja: no se puede reservar.» si `es_baja` (el de hoy), y si
    no «El cartel está fuera de servicio (<estado>): no se puede reservar hasta que vuelva a un
    estado operativo.».
  - `reservas_vigentes_del_cartel(cartel, dia=None)`: Pendientes y Confirmadas con
    `fecha_fin >= hoy` (hora de Argentina), ordenadas por fecha de inicio. Es la lista de
    «reservas activas» del criterio 1.
- **Alta y edición individual (`ReservaSerializer.validate`):** la validación `es_baja` actual pasa
  a llamar a `validar_cartel_reservable`. Se mantiene el criterio de hoy: se valida al crear y al
  **cambiar** de cartel; una reserva que ya estaba en ese cartel se puede seguir editando
  (fechas, precios, confirmar), porque la regla dice «sin modificarlas».
- **Reserva masiva:** `_crear_en_tanda` usa el mismo servicio (la fila sale en `fallidas` con el
  mensaje) y `carteles_para_tanda` filtra `estado__operativo=True`, así «Agregar carteles» no los
  ofrece.
- **Lista de reservas:** filtro nuevo `?vigentes=1` en `/api/reservas/`, que se combina con
  `?cartel=<id>` y llama a `reservas_vigentes_del_cartel`.
- **Inventario:** `CartelSerializer` suma `operativo` (solo lectura, desde `estado.operativo`).
- **Frontend:**
  - `CartelesPage`: al guardar un cartel cuyo estado nuevo no es operativo, pide
    `/api/reservas/?cartel=<id>&vigentes=1`; si hay reservas, abre un aviso «El cartel quedó
    <estado> y tiene N reservas activas» con la tabla (reserva, campaña, fechas, estado). El
    guardado no se frena: es un aviso. También aparece al usar «Dar de baja».
  - `ReservaForm`: el selector de cartel ofrece solo los operativos (hoy filtra los de baja) y
    muestra «(fuera de servicio)» en el cartel ya guardado si dejó de serlo, como hace con «(de
    baja)».
- **Docs:** columna «Dónde vive» de RN-010 y el manual de uso (carteles y reservas).

## Fuera de alcance

- Mover o cancelar solas las reservas afectadas (RN-010 dice no modificarlas).
- Notificaciones por correo o al administrador.
- Marcar los carteles no operativos en Disponibilidad y en el calendario (siguen apareciendo como
  hoy; se puede pedir como ajuste).
- Bloquear la confirmación de una Pendiente que ya estaba en el cartel.

## Migraciones

Ninguna: `operativo` ya existe.

## Reglas provisorias que se usan

- RN-010: alertar y listar las reservas afectadas, sin modificarlas, y bloquear reservas nuevas
  mientras el cartel no esté operativo.

## Cómo se prueba

Backend (pytest contra PostgreSQL, `@pytest.mark.regla("RN-010")`):

- `test_crear_reserva_cartel_no_operativo_rechaza` (criterio 2), con mensaje claro.
- `test_crear_reserva_cartel_vuelve_a_activo_permite` (criterio 3).
- `test_mover_reserva_a_cartel_no_operativo_rechaza` y
  `test_editar_reserva_en_cartel_no_operativo_permite` (sin modificarlas).
- `test_reserva_en_bloque_cartel_no_operativo_queda_fallida` y
  `test_carteles_para_tanda_cartel_no_operativo_no_aparece`.
- `test_listar_reservas_vigentes_del_cartel_devuelve_activas` (criterio 1): excluye Canceladas,
  Finalizadas y las que terminaron antes de hoy.
- El test de cartel de baja que ya existe sigue pasando con el mismo mensaje.

Frontend (Vitest):

- `CartelesPage`: al pasar un cartel a un estado no operativo con reservas vigentes, se muestra el
  aviso con la tabla; sin reservas, no se muestra; a un estado operativo, no se consulta.
- `ReservaForm`: el selector no ofrece carteles no operativos.

## Registro de gates

- Gate 1 (plan): 2026-10-29 — aprobado por Juan Diego
- Ajustes durante la implementación: el mensaje dice «fuera de servicio (<estado>)» porque «está
  Vidrio destruido» no se lee bien; la campaña del aviso va como texto, sin enlace, porque la app no
  tiene una URL por campaña. El aviso queda en `features/reservas/ReservasAfectadas.tsx`.
- Gate 2 (verificación): pendiente
- Gate 3 (PR): pendiente
