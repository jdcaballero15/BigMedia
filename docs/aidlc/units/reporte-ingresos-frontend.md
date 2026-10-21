# Unidad: Pantalla del reporte de ingresos

- **Estado:** en curso · **Épica:** E8 Reportes y paneles · **App dueña:** `frontend` (+ `facturacion`)
- **Origen:** HU-049 (pantalla) · **Rama:** `feature/frontend-reporte-ingresos`

## Objetivo

Darle a gerencia la pantalla del reporte de ingresos: una tabla con el ranking de clientes (agencias),
expandible a sus marcas, con el desglose mensual por período y los totales, consumiendo
`GET /api/facturacion/ingresos/` (HU-049). Cierra la parte visible de HU-049, cuyo backend ya está
mergeado (`reporte-ingresos`).

## Decisiones de diseño (mi criterio — corregir acá si hace falta)

1. **Importes como string en el endpoint.** Hoy `GET /api/facturacion/ingresos/` emite los montos como
   número (float) porque la vista devuelve `Decimal` por `Response`. El reporte de costos los emite
   como string y la regla 5 pide `Decimal` para dinero. Ajuste chico en `facturacion`: el servicio
   formatea los importes a string de 2 decimales antes de responder. Es el contrato que consume la
   pantalla. (Toca la app `facturacion`, ya mergeada, pero es su propio contrato.)
2. **Dónde vive la pantalla:** nueva feature `frontend/src/features/facturacion/`, calcando el patrón
   de las páginas existentes (`apiGet`, `section-heading`, `filters card`, `card table-wrap`).
3. **Navegación:** se agrega una sección **"Reportes"** en la barra lateral (`App.tsx`) con el ítem
   **"Ingresos"** (ícono de lucide, p. ej. `TrendingUp`). No se mueve nada existente.
4. **Layout:** filtros de período (Desde/Hasta con `input type="month"`, por defecto el año actual) +
   una tabla con una columna por mes del período y una de Total. Cada cliente es una fila (ranking por
   total, como ya ordena el backend); al tocarla se despliegan sus marcas. Fila final con el total
   global.
5. **Formato de dinero:** se muestra con separador de miles y 2 decimales (`Intl.NumberFormat`
   es-AR), prefijo `$`. Helper local `formatearMonto` en la feature.
6. **Visibilidad:** el ítem aparece para cualquier usuario con sesión (el endpoint todavía no cierra
   los ingresos a "Gerencia"; ese cierre quedó atado a HU-052, fuera de esta unidad).

## Cambios

- **Backend** (`backend/apps/facturacion/services.py`): los importes (`total` global, `total` y
  `por_mes` de clientes y marcas) salen como `str` de 2 decimales. Sin cambios de contrato en las
  claves. Se reverifican los tests de `test_reporte_ingresos.py` (ya comparan con `Decimal(str(...))`,
  siguen pasando).
- **Frontend:**
  - `src/features/facturacion/types.ts`: tipos `ReporteIngresos`, `ClienteFila`, `MarcaFila`, `Periodo`.
  - `src/features/facturacion/montos.ts`: `formatearMonto(valor: string): string`.
  - `src/features/facturacion/ReporteIngresos.tsx`: la pantalla (filtros + tabla expandible + total).
  - `src/features/facturacion/ReporteIngresos.test.tsx`: tests con `fetch` mockeado.
  - `src/App.tsx`: sección "Reportes" con el ítem "Ingresos".

## Reglas (HU-049)

Ninguna nueva. Consume el reporte que ya aplica RN-014 en el backend.

## Migraciones

Ninguna.

## Reglas que se usan

Ninguna del catálogo se reubica; la pantalla solo muestra lo que el backend ya calcula.

## Cómo se prueba

- Frontend (`ReporteIngresos.test.tsx`, Vitest + Testing Library, `fetch` mockeado):
  - muestra el ranking de clientes en el orden del backend, con las columnas de meses y los totales.
  - al desplegar un cliente, aparecen sus marcas.
  - al cambiar el período, vuelve a pedir el reporte con los nuevos `desde`/`hasta`.
  - importes formateados (miles y 2 decimales); estado vacío cuando no hay ingresos; alerta ante error.
- Backend: `pytest` de `test_reporte_ingresos.py` sigue en verde con los importes como string.
- Verificación completa: `format:check`, `lint`, `typecheck`, `test:coverage` (umbral 80 %), `build`
  en el frontend; y toda la batería del backend.

## Registro de gates

- Gate 1 (plan): 2026-10-20 — aprobado (importes del endpoint a string; pantalla en `facturacion`;
  sección "Reportes" en la barra; visible para cualquier usuario con sesión).
- Gate 2 (verificación): 2026-10-20 — Frontend: `format:check`, `lint`, `typecheck` en verde;
  `test:coverage` 85 pasan (cobertura líneas 89 %, sentencias 86 %, umbral 80 %); `build` ok.
  Backend: `ruff format --check`, `ruff check`, `makemigrations --check` y gitleaks en verde;
  `pytest --cov` 247 pasan, cobertura total 94.64 %.
- Gate 3 (PR): —
