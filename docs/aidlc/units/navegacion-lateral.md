# Unidad: Navegación lateral

- **Estado:** mergeada · **Épica:** — (unidad técnica de interfaz) · **App dueña:** frontend (y `costos` para la lista)
- **Origen:** pedido de Juan Diego del 19/10/2026 · **Rama:** `feature/frontend-navegacion-lateral`

## Objetivo

Pasar el menú de arriba a una barra vertical a la izquierda, agrupada en secciones con íconos, darle
pantalla propia a Proveedores, Formatos y Costos, y dejar lugar para el panel principal (HU-047).

## Decisiones tomadas con Juan Diego (19/10/2026)

- **Secciones:** Panel, Comercial, Inventario, Operación y Configuración.
- **Costos:** la sección Costos lista todos los costos cargados. Se siguen cargando desde la reserva.
- **Íconos:** con `lucide-react`.
- **Panel:** es la sección "dashboard". Su contenido es HU-047 y va en la unidad siguiente,
  `panel-principal`, para no mezclar el rediseño del menú con cálculos nuevos.

## Cambios

- **Menú (`App.tsx`, `App.css`):** barra lateral fija a la izquierda, con la marca arriba, el
  usuario y "Salir" abajo. En pantallas chicas se pliega detrás de un botón de menú. Secciones e ítems:

  | Sección | Ítems |
  | --- | --- |
  | Panel | Inicio (se agrega en `panel-principal`) |
  | Comercial | Clientes, Marcas, Campañas |
  | Inventario | Carteles, Disponibilidad |
  | Operación | Proveedores, Costos, Formatos |
  | Configuración | Catálogos (Departamentos y Estados físicos) |

  Hasta que exista el panel, la app abre en Clientes.
- **Proveedores y Formatos:** salen de Catálogos y tienen pantalla propia. Se reusa el mismo
  componente de catálogo con las categorías que corresponden a cada pantalla, sin cambiar cómo se
  cargan ni se editan.
- **Costos (pantalla nueva, `features/costos/CostosPage.tsx`):** tabla con fecha, campaña, cartel,
  tipo, proveedor, monto y estado (anulado o no), filtrable por tipo y proveedor, con el total de los
  no anulados. Solo lectura: el alta y la anulación siguen en la reserva.
- **Backend `costos`:** la lista suma dos campos de solo lectura, el cartel y la campaña de la
  reserva, y acepta los filtros `tipo` y `proveedor`. Sin cambios de modelo.
- **Dependencia nueva:** `lucide-react` en el frontend.

## Migraciones

Ninguna.

## Reglas provisorias que se usan

Ninguna.

## Cómo se prueba

- Backend: la lista de costos devuelve cartel y campaña; los filtros `tipo` y `proveedor` filtran;
  un filtro con un ID no numérico se rechaza.
- Frontend (Vitest): el menú muestra las secciones y cambia de pantalla; Catálogos ya no ofrece
  Proveedores ni Formatos; Proveedores y Formatos tienen su pantalla; Costos lista, filtra y suma.
  La cobertura se mantiene ≥ 80 %.
- Prueba manual en local: recorrer todas las pantallas desde el menú, en ancho de escritorio y de celular.

## Registro de gates

- Gate 1 (plan): 2026-10-19 — aprobado por Juan Diego
- Gate 2 (verificación): 2026-10-19 — aprobado por Juan Diego tras probarlo en local. ruff y mypy sin observaciones (77 archivos); sin migraciones pendientes; pytest 223 tests contra PostgreSQL, cobertura 94,42 %; frontend format, lint, typecheck y build OK, 79 tests, cobertura 85,78 % sentencias / 88,77 % líneas.
- Gate 3 (PR): #22
