# Unidad: cliente-que-factura

- **Estado:** en revisión · **Épica:** E4 Campañas · **App dueña:** campanias
- **Origen:** HU-027 (criterio 3), RN-014 · **Rama:** `feature/campanias-cliente-que-factura`

## Objetivo

Que cambiar el cliente de una marca no reescriba el histórico: las campañas que ya existían
conservan el cliente que las facturaba (HU-027, criterio 3).

## Encuadre

- **RN-014 (`provisoria`, Seba 2026-10-19):** la campaña lleva un cliente que factura propio y
  opcional (`Campania.cliente_facturacion`) que reemplaza la deducción desde la marca. Los criterios
  1 y 2 de HU-027 ya están hechos en la unidad [campanias](campanias.md) (`Campania.cliente_factura`);
  esa unidad dejó el criterio 3 para una unidad propia.
- **App dueña:** `campanias`, que es donde se escribe. El cambio lo dispara la edición de una marca, en
  `clientes`, que no puede importar de `campanias`. Gonza eligió (2026-11-03) una señal propia de
  `clientes` que escucha `campanias`, con [ADR-0010](../../adr/0010-senal-cliente-de-marca-cambiado.md).
- **Capas:** solo backend (`clientes`: señal, servicio, vista y admin; `campanias`: receptor y
  servicio). Sin cambios de frontend: el formulario de marca ya permite cambiar el cliente.

## Cambios

- **clientes:**
  - `apps/clientes/signals.py`: `cliente_de_marca_cambiado = Signal()`, con `marca` y
    `cliente_anterior`.
  - Servicio `actualizar_marca(marca, cliente_anterior_id)` en `apps/clientes/services.py`: si el
    cliente cambió, emite la señal. `MarcaViewSet.perform_update` guarda y llama al servicio dentro de
    `transaction.atomic()`, así el estampado y el cambio de la marca quedan juntos o no queda ninguno.
  - `MarcaAdmin.save_model` hace lo mismo, para que el cambio desde `/admin/` también estampe.
- **campanias:**
  - Servicio `estampar_cliente_anterior(marca, cliente_anterior)`: a **todas** las campañas de la
    marca sin cliente propio (`cliente_facturacion` vacío), en cualquier estado, les pone
    `cliente_facturacion = cliente_anterior`. Las que ya tienen cliente propio no se tocan. Registra
    en auditoría el cambio de `cliente_facturacion` de cada campaña, con origen `sistema`.
  - Receptor en `apps/campanias/signals.py`, conectado en `CampaniasConfig.ready()`.
- **Docs:** ADR-0010, columna «Dónde vive» de RN-014 y una línea en el manual (ficha de marca: qué
  pasa al cambiar el cliente).

## Decisiones de Gonza (2026-11-03)

- Mecanismo: señal propia de `clientes` (no `pre_save` ni endpoint en `campanias`).
- Alcance: todas las campañas existentes sin cliente propio, sin mirar el estado. Si una cotizada
  tiene que pasar al cliente nuevo, se le saca el cliente propio a mano.

## Fuera de alcance

- Avisar en el formulario de marca cuántas campañas se van a estampar.
- Los ítems a facturar: ya guardan su propio cliente, así que no cambian.

## Migraciones

Ninguna: `Campania.cliente_facturacion` ya existe.

## Reglas provisorias que se usan

- RN-014: cliente propio opcional en la campaña que reemplaza la deducción desde la marca.

## Cómo se prueba

`backend/tests/test_cliente_que_factura.py`, contra PostgreSQL, con `@pytest.mark.regla("RN-014")`:

- cambiar el cliente de una marca por el PATCH estampa el cliente anterior en sus campañas sin
  cliente propio, de cualquier estado (criterio 3);
- la campaña que ya tenía cliente propio lo conserva;
- editar la marca sin cambiar el cliente no estampa nada;
- después del cambio, una campaña nueva de la marca factura al cliente nuevo;
- el estampado queda en auditoría con origen `sistema`;
- si el estampado falla, el cambio de la marca no se guarda (transacción);
- el cambio desde el admin también estampa, y el alta desde el admin crea la marca.

## Registro de gates

- Gate 1 (plan): 2026-11-03 — aprobado por Gonza
- Gate 2 (verificación): 2026-11-03 — `ruff format --check` y `ruff check` sin errores; `mypy backend`
  sin errores (145 archivos); `makemigrations --check` sin cambios; `pytest --cov` 908 passed, 97,21 %
  (más el test de alta de marca desde el admin, agregado después y corrido aparte con
  `test_clientes_admin.py`: 19 passed); frontend: `format:check`, `lint`, `typecheck`,
  `test:coverage` (395 tests, 92,75 % de sentencias, 94,77 % de líneas) y `build` en verde;
  `pre-commit run --all-files` en verde, gitleaks incluido.
- Gate 3 (PR): #115
