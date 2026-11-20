# Unidad: ajuste-interacciones-en-ficha-cliente

- **Estado:** en revisión · **Épica:** E3 Clientes, marcas y CRM · **App dueña:** frontend
- **Origen:** pedido de Gonza (2026-11-19), HU-020, HU-021 · **Rama:** `feature/frontend-interacciones-en-ficha-cliente`

## Objetivo

Sacar la pantalla **Comercial › Interacciones** del menú y cargar y editar las interacciones desde
la pestaña **Interacciones** de la ficha del cliente (Clientes › Ver ficha), que hoy es de solo
lectura.

## Decisiones (Gonza, 2026-11-19)

- En la ficha se puede **cargar y editar**, solo con permiso de edición (`usePuedeEditar`).
- Al cargar desde la ficha, el **cliente queda fijo** en el de la ficha; se eligen contacto,
  campaña y marca de ese cliente.
- Las listas de solo lectura del **detalle de campaña** y de la **ficha de marca** quedan como
  están.

## Cambios

- frontend, `App.tsx`: se saca el ítem «Interacciones» del grupo Comercial y su tipo de pantalla.
- frontend, `features/campanias/InteraccionesPage.tsx`: se borra, con su test.
- frontend, `features/campanias/InteraccionForm.tsx`: recibe el cliente de la ficha (`cliente`)
  en lugar de la lista de clientes, y lo muestra sin poder cambiarlo. Al implementar se vio que
  `InteraccionesPage` era la única pantalla que lo usaba, así que el selector de cliente se saca
  en vez de quedar detrás de una prop opcional.
- frontend, `features/campanias/InteraccionesLista.tsx`: prop opcional `clienteParaCargar`:
  botón «Nueva interacción», «Editar» por fila, alta con `POST` y edición con `PATCH` a
  `/api/campanias/interacciones/`, y vuelve a cargar la lista y el contador de la ficha al
  guardar. Sin esa prop sigue de solo lectura (campaña y marca).
- frontend, `features/clientes/FichaCliente.tsx`: la pestaña Interacciones usa la lista con
  edición cuando el rol puede editar.
- docs, `docs/manual/manual-de-uso.md`: el menú Comercial ya no tiene Interacciones y se explica
  que se cargan desde la ficha del cliente.

Backend: sin cambios. La API y sus validaciones (RN-015, RN-018) quedan iguales.

## Migraciones

Ninguna.

## Reglas provisorias que se usan

Ninguna. HU-020 no dice desde qué pantalla se carga; sus criterios siguen valiendo.

## Cómo se prueba

- Los tests de `InteraccionesPage.test.tsx` que siguen valiendo pasan a la lista y a la ficha:
  - alta con `POST` desde la ficha, con el cliente fijo, y recarga de la lista;
  - edición con `PATCH`;
  - el rol Lectura no ve «Nueva interacción» ni «Editar»;
  - «Sin asunto», vacío y error de carga;
  - las listas de campaña y de marca siguen sin botones.
- `InteraccionForm.test.tsx`: con el cliente fijo no se puede cambiar el cliente, y se cargan sus
  contactos, campañas y marcas.
- `App.test.tsx`: el menú Comercial ya no muestra «Interacciones».
- Verificación completa de la Definition of Done (`CLAUDE.md` §7).

## Registro de gates

- Gate 1 (plan): 2026-11-19 — aprobado por Gonza
- Gate 2 (verificación): 2026-11-19 — `ruff format --check` (145 archivos ya formateados) y
  `ruff check` (All checks passed!); `mypy backend` (no issues found in 145 source files);
  `makemigrations --check --dry-run` (No changes detected); `pytest --cov` (914 passed, 97.49 %,
  ninguno salteado); `pre-commit run --all-files` con gitleaks (13 hooks Passed); frontend
  `format:check`, `lint`, `typecheck` sin errores, `test:coverage` (433 passed; sentencias
  92.67 %, ramas 83.74 %, líneas 94.62 %) y `build` (built in 1.18s). Aprobado por Gonza
  (2026-11-19).
- Gate 3 (PR): #150
