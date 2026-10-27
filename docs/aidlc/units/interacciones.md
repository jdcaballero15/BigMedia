# Unidad: Interacciones comerciales

- **Estado:** mergeada · **Épica:** E3 Clientes, marcas y CRM · **App dueña:** `campanias`
- **Origen:** HU-020, más los criterios 5 y 7 de HU-068 · **Rama:** `feature/campanias-interacciones`

## Objetivo

Registrar las reuniones y llamadas comerciales con asunto, fecha, notas, cliente, el contacto del
intermediario formal si lo hubo y, de forma opcional, la campaña. Así no se pierde el rastro de
las conversaciones. Las interacciones tienen una sección propia en el menú, dentro de **Comercial**,
y además aparecen en la ficha del cliente y en el detalle de la campaña.

## Decisiones

1. **Sección propia en Comercial** (Juan Diego, 26/10/2026): un ítem **Interacciones** en el grupo
   Comercial del menú, junto a Clientes, Marcas y Campañas, relacionado con cliente, contacto y
   campaña opcional.
2. **El modelo vive en la app `campanias`** (propuesta). `docs/arquitectura.md` pone las
   interacciones en `clientes`, pero una interacción puede llevar una campaña y `clientes` no puede
   importar de `campanias`. `campanias` ya importa de `clientes`, así que ahí el modelo apunta a
   `Cliente`, `Contacto` y `Campania` sin crear ninguna dependencia nueva entre apps. Se actualiza
   la tabla de apps de `docs/arquitectura.md` para que diga dónde viven.
3. **Tipo de interacción** (propuesta): Reunión o Llamada, que son las dos que nombra la historia.
   Es obligatorio; el formulario propone Llamada.
4. **Campaña relacionada con el cliente** (propuesta): si se indica una campaña, tiene que ser una
   campaña que el cliente factura o de una marca del cliente. Evita colgar una conversación de una
   campaña ajena por error.
5. **Contacto** (HU-068, criterio 5): solo se puede elegir un contacto **activo** del mismo cliente.
   Al editar una interacción vieja, se conserva el contacto aunque después se haya inactivado.
6. **Sin borrado** (HU-006): las interacciones se crean y se editan, no se borran. La API no expone
   `DELETE`, igual que en clientes, marcas y contactos.
7. **Quién la registró**: se guarda el usuario que la cargó, automáticamente. No se edita.
8. **Fuera de alcance**: el vínculo con una marca espera la respuesta de Seba (RN-018, pregunta
   12). La ficha completa del cliente es HU-021.

## Cambios

- `campanias/models.py`: modelo `Interaccion` con `tipo`, `asunto` (obligatorio), `fecha`
  (obligatoria), `notas`, `cliente` (obligatorio), `contacto` (opcional), `campania` (opcional),
  `registrada_por`, `creado_en` y `actualizado_en`. Orden por fecha descendente (criterio 3).
- `campanias/services.py`: las reglas de las decisiones 4 y 5.
- `campanias/serializers.py`, `views.py` y `urls.py`: `InteraccionSerializer` y
  `InteraccionViewSet` en `/api/campanias/interacciones/`, con GET, POST y PATCH, filtros por
  `cliente` y `campania`, y los mismos permisos que campañas (Operativo edita; Lectura y Gerencia
  solo leen).
- `campanias/admin.py`: registro del modelo.
- Frontend:
  - `features/campanias/InteraccionesPage.tsx` (nuevo): la sección del menú, con la lista
    (fecha, tipo, asunto, cliente, contacto, campaña) y un filtro por cliente.
  - `features/campanias/InteraccionForm.tsx` (nuevo): alta y edición. Al elegir el cliente, ofrece
    sus contactos activos (si es intermediario formal) y sus campañas.
  - `features/campanias/InteraccionesLista.tsx` (nuevo): la lista reutilizable que se muestra en la
    ficha del cliente (`ClientesPage`) y en el detalle de la campaña (`CampaniaDetalle`).
  - `App.tsx`: el ítem Interacciones en el grupo Comercial.
- `docs/arquitectura.md`: las interacciones pasan de `clientes` a `campanias` en la tabla de apps.

## Migraciones

`campanias.0003_interaccion`: crea la tabla. No mueve datos.

## Reglas provisorias que se usan

Ninguna. RN-018 (interacciones antes de la campaña) sigue `pendiente` y no se implementa.

## Cómo se prueba

En `backend/tests/test_interacciones.py`:

- `test_interaccion_sin_asunto_se_rechaza` (criterio 1), y lo mismo sin fecha y sin cliente.
- `test_interaccion_con_cliente_y_campania_aparece_en_ambos_filtros` (criterio 2).
- `test_lista_ordenada_por_fecha_descendente` (criterio 3).
- `test_contacto_inactivo_no_se_puede_elegir` y `test_contacto_inactivado_se_conserva_en_la_pasada`
  (HU-068, criterio 5).
- `test_contacto_de_otro_cliente_se_rechaza` y `test_campania_ajena_al_cliente_se_rechaza`.
- `test_registrada_por_se_completa_con_el_usuario`.
- `test_lectura_no_puede_crear` y `test_no_hay_delete`.

En el frontend: tests de `InteraccionForm` (obligatorios, contactos activos del cliente elegido,
envío), de `InteraccionesPage` (lista y filtro) y de la lista en la ficha del cliente y en el detalle
de la campaña.

A mano en `localhost`: cargar una llamada con un contacto de un intermediario formal y una
campaña, y verla en la sección, en la ficha del cliente y en la campaña.

## Pendiente fuera de esta unidad

- Esta rama sale de `develop` sin el selector de fechas (PR #71): el formulario usa el campo de fecha
  del navegador y las tablas muestran `aaaa-mm-dd`. Cuando se mergee #71, pasar `InteraccionForm` a
  `CampoFecha` y las fechas de las tablas a `formatearFecha`.
- Agregado durante la implementación: filtro `?cliente=` en la lista de campañas, para que el
  formulario ofrezca solo las campañas del cliente elegido (decisión 4).

## Registro de gates

- Gate 1 (plan): 2026-10-27 — aprobado por Juan Diego
- Gate 2 (verificación): 2026-10-27 — backend: `ruff format --check` y `ruff check` ok, `mypy` sin
  errores en 117 archivos, `makemigrations --check` sin cambios, `pytest --cov` 518 en verde
  (96,14 %). Frontend: `format:check` ok, `lint` y `typecheck` sin errores, `test:coverage` 193 en
  verde (sentencias 88,38 %, líneas 91,39 %), `build` ok. `pre-commit run --all-files` en verde,
  gitleaks incluido. La prueba a mano en `localhost` quedó sin resultado informado: Juan Diego
  pidió el PR directamente.
- Gate 3 (PR): 2026-10-27 — pedido por Juan Diego; [PR #73](https://github.com/jdcaballero15/BigMedia/pull/73) a `develop`.
