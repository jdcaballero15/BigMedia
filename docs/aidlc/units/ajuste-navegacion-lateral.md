# Unidad: Ajuste de la navegación lateral

- **Estado:** en revisión · **Épica:** — (unidad técnica de interfaz) · **App dueña:** frontend
- **Origen:** pedido de Juan Diego del 08/11/2026 · **Rama:** `feature/frontend-menu-expandible`

## Objetivo

Que el menú lateral muestre el nombre de cada pantalla y el título de cada sección, y que se pueda
contraer a solo iconos y volver a expandir. Hoy solo tiene iconos, y el nombre aparece únicamente
al pasar el mouse, así que cuesta saber a dónde lleva cada uno.

Cambia la decisión 4 de [`estilo-base`](estilo-base.md) («menú lateral solo con iconos»): el modo
solo iconos pasa a ser el estado contraído, que elige cada persona.

## Decisiones tomadas con Juan Diego (08/11/2026)

- **Estado inicial:** expandido, con iconos y nombres.
- **Títulos de sección:** sí, un rótulo chico en gris arriba de cada grupo (Comercial, Inventario,
  Operación, Configuración…). Contraído vuelve a ser la línea divisoria de hoy.
- **Recordar la elección:** sí, en ese navegador (`localStorage`). Si el navegador no lo deja
  guardar, el menú arranca expandido y funciona igual.

## Cambios

- **`App.tsx`:**
  - Nuevo estado `menuContraido`, leído y guardado en `localStorage` (clave
    `bigmedia.menu-contraido`), con `try/catch` en la lectura y la escritura.
  - Arriba del menú: la marca «BM» más el texto «Big Media» y un botón para contraer o expandir
    (iconos `PanelLeftClose` y `PanelLeftOpen` de `lucide-react`, ya instalado). El botón lleva
    `aria-label` «Contraer menú» o «Expandir menú» y `aria-expanded`.
  - Expandido: cada sección muestra su título y cada botón, su icono y su nombre. El tooltip deja
    de aparecer, porque el nombre ya se ve.
  - Contraído: queda como hoy, con los iconos solos y el nombre en el tooltip y en `aria-label`.
  - El usuario y «Salir» siguen abajo. Expandido, se ve el nombre del usuario al lado de la inicial.
- **`App.css`:**
  - `--ancho-menu` pasa a 232 px expandido y queda en 76 px contraído, con la clase
    `menu-contraido` en `.app-shell`.
  - Estilos nuevos para el título de sección, el botón de contraer y la fila icono + nombre.
  - Celular (≤ 900 px): sigue el menú desplegable de hoy, con los nombres a la vista. Se suman los
    títulos de sección y se oculta el botón de contraer, porque ahí no aplica.
- **Manual (`docs/manual/manual-de-uso.md`):** «Cómo está organizada la pantalla» describe el menú
  con nombres y el botón para contraerlo.

Fuera de alcance: cambiar las secciones, el orden de los ítems o los iconos.

## Migraciones

Ninguna. No hay cambios en el backend.

## Reglas provisorias que se usan

Ninguna.

## Cómo se prueba

- Frontend (Vitest, `App.test.tsx`):
  - El menú arranca expandido: se ven los títulos de sección y el nombre de cada pantalla,
    y el botón dice «Contraer menú» con `aria-expanded="true"`.
  - Contraer el menú: cambia la clase de `.app-shell`, el botón pasa a «Expandir menú» y lo
    guarda en `localStorage`. Al volver a montar `App`, arranca contraído.
  - Contraído, el tooltip con el nombre sigue apareciendo al pasar el mouse o con el foco. Este
    test reemplaza al actual de tooltip. Expandido, no aparece.
  - Si `localStorage` tira error, el menú arranca expandido y se puede contraer igual.
  - Los tests existentes de navegación siguen pasando y la cobertura se mantiene ≥ 80 %.
- Prueba manual en local: expandir, contraer y recargar en ancho de escritorio, y abrir el menú
  en ancho de celular.

## Registro de gates

- Gate 1 (plan): 2026-11-08 — aprobado por Juan Diego
- Gate 2 (verificación): 2026-11-08 — aprobado por Juan Diego tras probarlo en local. ruff format y check sin observaciones (146 archivos); mypy sin errores (146 archivos); sin migraciones pendientes; pytest 918 tests contra PostgreSQL, ninguno salteado, cobertura 97,27 %; pre-commit (incluye gitleaks) sin hallazgos; frontend format, lint, typecheck y build OK, 398 tests, cobertura 92,79 % sentencias / 94,79 % líneas.
- Gate 3 (PR): #125
