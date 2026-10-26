# Unidad: Contactos del intermediario formal

- **Estado:** mergeada · **Épica:** E3 Clientes, marcas y CRM · **App dueña:** `clientes`
  (+ `frontend`)
- **Origen:** HU-068 (RN-015) · **Rama:** `feature/clientes-contactos-intermediario`

## Objetivo

Que un cliente de tipo intermediario formal tenga varios contactos (nombre, cargo o área, correo,
teléfono y notas), con un único contacto principal, y que esos contactos se inactiven y nunca se
borren (HU-068, criterios 1 a 4 y 6).

## Punto de partida (relevamiento del 26/10/2026)

- `Cliente.Tipo` ya tiene `INTERMEDIARIO_FORMAL` (`apps/clientes/models.py`), pero ningún modelo de
  contacto. El cliente solo tiene su propio `telefono` y `correo`.
- La API de `clientes` usa rutas planas con filtro (`/api/clientes/marcas/?cliente=<id>`) y
  `ClientesBaseViewSet`: lee cualquiera con sesión, edita Operativo, sin `DELETE`, con
  `incluir_inactivos` para ver los inactivos.
- La "ficha" de hoy es `MarcasDelCliente` en `ClientesPage.tsx`: se abre al editar un cliente y
  muestra sus marcas. Ahí entra la sección de contactos.
- `config/admin_borrado.BorradoAuditadoAdmin` (HU-006) ya permite que el superusuario borre una
  carga errónea, con auditoría.
- **RN-015 sigue `provisoria`**, con el valor "tipo aparte con contactos múltiples", a la espera de
  Seba. Qué datos lleva el contacto sale de la regla de negocio de HU-068.
- **HU-020 (interacciones) y HU-021 (ficha completa) no existen todavía.** Los criterios 5 (el
  contacto inactivo no se ofrece en una interacción) y 7 (la ficha muestra el contacto de cada
  interacción) dependen de ellas.

## Preguntas al equipo

1. **Ruta de la API.**
   - a) **Plana, como marcas:** `/api/clientes/contactos/?cliente=<id>`, con `POST` y `PATCH` y sin
     `DELETE`. **(recomendado)**
   - b) Anidada: `/api/clientes/clientes/<id>/contactos/`. Rompe la convención del repo.
2. **Contacto principal (criterio 3).** Propuesta: al marcar uno como principal, el servicio
   desmarca al anterior en la misma transacción, con el cliente bloqueado (`select_for_update`).
   Una restricción única parcial en la base (`cliente` con `principal=True`) lo garantiza aunque
   dos personas guarden a la vez. Inactivar un contacto le saca la marca de principal. ¿Está bien?
3. **Tipo de cliente y contactos.**
   - a) **El servidor rechaza** cargar un contacto en un cliente que no es intermediario formal, y
     cambiar el tipo de un intermediario formal que tiene contactos activos responde 400 con
     "Inactivá antes sus contactos" (criterio 6). Los contactos inactivos no lo impiden.
     **(recomendado)**
   - b) Solo lo controla la pantalla.
4. **Criterios 5 y 7.** Propuesta: quedan para la unidad de HU-020, que es la que agrega las
   interacciones. Esta unidad deja listo el filtro de contactos activos (la API los lista sin los
   inactivos salvo con `incluir_inactivos=1`). ¿Está bien?
5. **Auditoría y admin.**
   - a) **Sin auditoría de cambios**: HU-007 audita reservas, campañas y tarifas, y los contactos
     no son datos de negocio de ese tipo. El contacto se registra en el admin con
     `BorradoAuditadoAdmin`, como cliente y marca, para corregir cargas erróneas.
     **(recomendado)**
   - b) Auditar cada cambio de contacto, como se hace con los usuarios.

## Respuestas

Respondidas por Gonza el 26/10/2026: se aceptan las opciones recomendadas o propuestas.

1. Ruta plana: `/api/clientes/contactos/?cliente=<id>`, sin `DELETE`.
2. Un solo principal: el servicio desmarca al anterior con el cliente bloqueado, más una
   restricción única parcial; inactivar saca el principal.
3. El servidor rechaza contactos en clientes que no son intermediario formal, y el cambio de tipo
   con contactos activos.
4. Los criterios 5 y 7 quedan para la unidad de HU-020.
5. Sin auditoría de cambios; el contacto va al admin con `BorradoAuditadoAdmin`.

## Cambios (con las opciones recomendadas)

- `backend/apps/clientes/models.py`: `Contacto` (`cliente` FK `PROTECT`, `nombre` obligatorio,
  `cargo`, `correo`, `telefono`, `notas`, `principal`, `activo`, fechas), con la restricción única
  parcial del principal.
- `backend/apps/clientes/services.py`: `guardar_contacto`, que desmarca al principal anterior e
  inactivar saca el principal; y el control de tipo del cliente.
- `backend/apps/clientes/serializers.py`, `views.py` y `urls.py`: `ContactoSerializer` y
  `ContactoViewSet`. `ClienteSerializer.validate` rechaza el cambio de tipo con contactos activos.
- `backend/apps/clientes/admin.py`: `ContactoAdmin` con `BorradoAuditadoAdmin`. El admin valida la
  restricción del principal y rechaza un segundo principal con su mensaje: hay que desmarcar antes
  al anterior. No pasa por `guardar_contacto`, porque Django valida las restricciones antes de
  guardar.
- `frontend/src/features/clientes/ContactosDelCliente.tsx` (nuevo) y `ContactoForm.tsx` (nuevo):
  la sección de contactos en la ficha, solo para intermediario formal, con alta, edición,
  "Marcar como principal" e "Inactivar".
- `frontend/src/features/clientes/ClientesPage.tsx` y `types.ts`: la sección en la ficha y el tipo
  `Contacto`.
- `docs/aidlc/reglas-de-negocio.md`: la columna "Dónde vive" de RN-015.

## Migraciones

Una en `clientes`: la tabla `Contacto` con su restricción. No toca datos existentes.

## Reglas provisorias que se usan

- RN-015 (`provisoria`): el intermediario formal es un tipo aparte, con contactos múltiples.

## Cómo se prueba

- `test_contacto_intermediario_formal_acepta_varios` (criterio 1, `@pytest.mark.regla("RN-015")`).
- `test_contacto_en_cliente_directo_o_intermediario_se_rechaza` (criterio 2, RN-015).
- `test_contacto_marcar_principal_desmarca_al_anterior` (criterio 3).
- `test_contacto_principal_concurrente_queda_uno_solo` (criterio 3, dos marcados a la vez).
- `test_contacto_sin_nombre_se_rechaza` (criterio 4).
- `test_contacto_inactivar_saca_el_principal_y_no_se_borra`.
- `test_contacto_lista_excluye_inactivos_salvo_pedido`.
- `test_cliente_cambio_de_tipo_con_contactos_activos_se_rechaza` y
  `test_cliente_cambio_de_tipo_con_contactos_inactivos_se_acepta` (criterio 6, RN-015).
- `test_contacto_delete_devuelve_405`.
- Además: cliente inactivo, cambio de cliente, correo inválido, inactivo como principal, orden de la
  lista, Lectura no edita, restricción en la base y los dos tests del admin
  (`test_clientes_admin.py`).
- Frontend: la sección aparece solo para intermediario formal; alta, principal e inactivar; el
  error del cambio de tipo se muestra.

## Registro de gates

- Gate 1 (plan): 26/10/2026 — aprobado por Gonza
- Gate 2 (verificación): corrida el 26/10/2026 — backend 494 tests, 96,02 %; frontend 180 tests; aprobado por Gonza el 26/10/2026
- Gate 3 (PR): 26/10/2026 — PR #70 a `develop`, pedido por Gonza
