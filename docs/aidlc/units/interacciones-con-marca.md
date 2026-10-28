# Unidad: interacciones-con-marca

- **Estado:** en curso · **Épica:** E3 Clientes, marcas y CRM · **App dueña:** campanias
- **Origen:** RN-018, HU-020 (criterios 4 y 5) · **Rama:** `feature/campanias-interacciones-con-marca`
- **Depende de:** el PR #95 (RN-018 en `provisoria`), que tiene que estar mergeado antes del PR de
  código.

## Objetivo

Que una interacción comercial pueda llevar una marca, para registrar las conversaciones sobre una
marca que todavía no tiene campaña, y que esas interacciones se vean en la ficha de la marca.

## Encuadre

- **RN-018 (`provisoria`, 2026-10-28):** marca opcional en la interacción. Tiene que ser una marca
  del cliente de la interacción y, si además hay campaña, la campaña tiene que ser de esa marca.
  Las interacciones previas no pasan solas a la campaña cuando se crea.
- **App dueña:** `campanias`, donde vive `Interaccion` (ADR-0006). Ya importa de `clientes`: sin
  dependencias nuevas entre apps.
- **Capas:** backend (`campanias`: modelo, servicio, serializer, vista) y frontend
  (`features/campanias` y la ficha de marca en `features/clientes`).

## Cambios

- **Modelo:** `Interaccion.marca`, `ForeignKey` a `Marca`, opcional (`null=True, blank=True`,
  `PROTECT`, `related_name="interacciones"`).
- **Servicio:** `validar_marca_de_interaccion(cliente, marca, campania, sin_cambios)` en
  `apps/campanias/services.py`:
  - la marca es del cliente (`marca.cliente_id == cliente.pk`); si no, error en `marca`;
  - la marca está activa, salvo que la interacción ya la tuviera (mismo criterio que el contacto,
    HU-068 criterio 5);
  - si hay campaña y marca, `campania.marca_id == marca.pk`; si no, error en `campania`.
- **Serializer:** campo `marca` y `marca_nombre` (solo lectura); `validate` llama al servicio nuevo
  junto con los de contacto y campaña.
- **Vista:** filtro `?marca=<id>` en la lista. Propuesta: devuelve las interacciones con esa marca
  **y** las que tienen una campaña de esa marca aunque no tengan la marca cargada, para que la
  ficha de la marca no quede vacía con las interacciones que ya existen.
- **Frontend:**
  - `InteraccionForm`: selector «Marca» opcional con las marcas activas del cliente
    (`/api/clientes/marcas/?cliente=`); la marca guardada se muestra aunque esté inactiva, como el
    contacto. Si hay marca elegida, el selector de campaña ofrece solo las campañas de esa marca.
    Al cambiar de cliente se vacía la marca, como hoy el contacto y la campaña.
  - `TablaInteracciones`: columna «Marca» (se puede ocultar, como cliente y campaña).
  - `InteraccionesLista`: acepta el filtro `{ marca }`.
  - Ficha de marca (`MarcasPage`): sección «Interacciones» con la lista filtrada por la marca, sin
    la columna Marca.
- **Docs:** columna «Dónde vive» de RN-018 y el manual de uso (interacciones y ficha de marca).

## Fuera de alcance

- Pasar interacciones a una campaña al crearla (RN-018 lo descarta).
- Filtro por marca en la pantalla general de Interacciones.

## Migraciones

`campanias.00xx_interaccion_marca`: agrega la columna nullable. Aditiva, sin mover datos.

## Reglas provisorias que se usan

- RN-018: marca opcional en la interacción, del mismo cliente y coherente con la campaña.

## Cómo se prueba

- Backend, en `backend/tests/test_interacciones.py`, con `@pytest.mark.regla("RN-018")`:
  - `test_crear_interaccion_con_marca_sin_campania_se_guarda`;
  - `test_crear_interaccion_con_marca_de_otro_cliente_se_rechaza`;
  - `test_crear_interaccion_con_campania_de_otra_marca_se_rechaza`;
  - `test_crear_interaccion_con_marca_inactiva_se_rechaza` y la edición que conserva una marca que
    después se inactivó;
  - `test_listar_interacciones_por_marca_incluye_las_de_sus_campanias`.
- Frontend: el formulario envía la marca y filtra las campañas por la marca elegida; la ficha de
  marca muestra sus interacciones.
- Revisión visual con Gonza en el navegador.
- Definition of Done completa.

## Registro de gates

- Gate 1 (plan): aprobado por Gonza el 2026-10-28, con el filtro de la ficha de marca propuesto.
- Gate 2 (verificación): 2026-10-28, ruff, mypy, makemigrations y pre-commit (gitleaks) limpios; pytest 797 passed, 96,92 %; frontend format, lint, typecheck, 369 tests (92,44 % sentencias, 94,43 % líneas) y build en verde. Revisión visual aprobada por Gonza el 2026-10-28. Rebaseada sobre develop con el PR #95 y columna «Dónde vive» de RN-018 completada.
- Gate 3 (PR):
