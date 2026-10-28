# Unidad: fichas-cliente-y-marca

- **Estado:** en curso · **Épica:** E3 Clientes, marcas y CRM · **App dueña:** frontend
- **Origen:** HU-021, HU-022 (criterio 1) · **Rama:** `feature/frontend-fichas-cliente-y-marca`

## Objetivo

Que desde un cliente se vean sus marcas, sus campañas y sus interacciones en una sola ficha, y que
desde una marca se vean todas sus campañas con su estado, sin importar quién las facturó.

## Encuadre

- **App dueña:** frontend. La API ya ofrece lo necesario: `GET /api/campanias/campanias/?cliente=<id>`
  (las que factura el cliente o las de sus marcas) y `?marca=<id>`.
- **Capas:** solo frontend (`features/campanias` y `features/clientes`). Sin cambios de backend.
- **Migraciones y reglas nuevas:** ninguna.

## Cambios

- `frontend/src/features/campanias/CampaniasLista.tsx` (nuevo): lista de solo lectura de campañas
  filtrada por `cliente` o por `marca`, con nombre, marca, cliente que factura, fechas y estado; con
  estados de carga, error y vacío. Mismo patrón que `InteraccionesLista`, y oculta la columna que ya
  da el contexto (la marca en su ficha).
- `ClientesPage.tsx`: la ficha del cliente suma la sección «Campañas de <cliente>» entre las marcas y
  las interacciones. El botón «Ver marcas» pasa a llamarse «Ver ficha».
- `MarcasPage.tsx`: nuevo botón «Ver ficha» por fila que abre la ficha de la marca con sus campañas
  (todos los estados, incluidas canceladas y perdidas) y un botón «Cerrar».

## Fuera de alcance

- HU-022 criterio 2 (marcas del mismo grupo económico): espera RN-016 (pregunta 16, `pendiente`).
- Campañas con cliente de facturación propio que es otro (HU-027, `Could`): la ficha del cliente
  muestra lo que ya devuelve el filtro `cliente` y la columna «Cliente que factura» lo aclara.
- Sin navegación a la campaña desde la ficha ni rutas nuevas (la app no usa router).

## Reglas provisorias que se usan

- RN-014 (quién factura: cliente propio de la campaña o, si no hay, el de la marca), ya resuelta en
  `cliente_factura` del serializer; solo se muestra.

## Cómo se prueba

- `CampaniasLista.test.tsx`: pide la URL con el filtro correcto; muestra filas con su estado; muestra
  «Sin campañas» cuando la lista está vacía (HU-021 criterio 3); muestra el error si falla la API;
  oculta la columna indicada.
- `ClientesPage.test.tsx`: al abrir la ficha se ven marcas, campañas e interacciones (HU-021 criterios
  1 y 2); un cliente sin campañas muestra las secciones vacías sin errores (criterio 3).
- `MarcasPage.test.tsx`: «Ver ficha» muestra las campañas de la marca con su estado, incluida una
  cancelada (HU-022 criterio 1); «Cerrar» la oculta.
- Definition of Done completa (backend sin cambios, pero se corre igual).

## Registro de gates

- Gate 1 (plan): 2026-10-27 — aprobado por Juan Diego
- Gate 2 (verificación): 2026-10-27 — `ruff format --check`: 135 files already formatted;
  `ruff check`: All checks passed!; `mypy backend`: Success: no issues found in 135 source files;
  `makemigrations --check --dry-run`: No changes detected; `pytest --cov`: 768 passed, coverage
  96.89 % (requerido 80 %); `pre-commit run --all-files`: todos Passed (incluido gitleaks).
  Frontend: `format:check` OK, `lint` sin hallazgos, `typecheck` OK, `test:coverage` 336 passed
  (sentencias 91.25 %, ramas 81.63 %, líneas 93.69 %), `build` OK (aviso de bloque mayor a 500 kB,
  previo a esta unidad).
- Gate 3 (PR): pendiente
