# Unidad: Exportar reportes a PDF

- **Estado:** mergeada · **Épica:** E8 Reportes y paneles · **App dueña:** `frontend`
- **Origen:** HU-052 criterio 3 (PDF) · **Rama:** `feature/frontend-exportar-pdf`

## Objetivo

Que gerencia exporte a **PDF** los reportes de **Ingresos** y **Ocupación** para **adjuntarlos en un
mail**, prolijos: el PDF conserva **título, filtros aplicados y fecha de generación** (HU-052,
criterio 3). Cierra HU-052 (quedaban CSV ✓ y permiso ✓; falta el PDF).

## Decisiones de diseño (mi criterio — corregir acá si hace falta)

1. **PDF del lado del cliente, archivo descargable de un clic** (como el botón CSV), porque es para
   adjuntar en un mail: no sirve el diálogo de impresión del navegador.
2. **Dependencia nueva `jspdf` + `jspdf-autotable`** (punto a confirmar, el front es minimalista en
   deps). Es la forma estándar de generar un PDF con tabla en el navegador; la alternativa sin
   dependencia (`window.print()` + CSS de impresión) abre el diálogo de impresión y obliga a elegir
   "Guardar como PDF", menos directo para el flujo de mail.
3. **Encabezado del PDF:** título del reporte, una línea con los **filtros** (período Desde–Hasta; en
   Ocupación además Departamento y Modalidad) y **"Generado el <fecha>"**; debajo, la tabla
   (`jspdf-autotable`).
4. **Alcance:** botón "Exportar PDF" junto al de CSV en **Ingresos** y **Ocupación**. Mismas filas que
   el CSV (respeta los filtros).
5. **Nombre de archivo:** `<reporte>-<desde>-<hasta>.pdf`.
6. **Permiso:** el de Ingresos ya está cerrado a Gerencia (la pantalla se oculta); el PDF no agrega
   nada nuevo de seguridad.

## Cambios

- `frontend/package.json`: agrega `jspdf` y `jspdf-autotable`.
- `frontend/src/shared/pdf.ts`: `descargarPdf(nombreArchivo, titulo, subtitulos, columnas, filas)` y
  una función pura `lineasEncabezado(titulo, filtros, fecha)` para testear el encabezado sin el DOM.
- `frontend/src/features/facturacion/ReporteIngresos.tsx` y
  `frontend/src/features/reservas/ReporteOcupacion.tsx`: botón "Exportar PDF".
- Tests: `pdf.test.ts` (encabezado puro) y, en cada pantalla, que el botón "Exportar PDF" dispara la
  descarga (se mockea el módulo `pdf`).

## Reglas

- **HU-052 (cierra).** Criterio 3 cumplido (PDF con título, filtros y fecha). Con esta unidad HU-052
  queda completa (CSV + permiso + PDF).

## Migraciones

Ninguna.

## Cómo se prueba

- Frontend:
  - `pdf.test.ts`: `lineasEncabezado` arma el título, la línea de filtros y "Generado el <fecha>".
  - `ReporteIngresos.test.tsx` / `ReporteOcupacion.test.tsx`: el botón "Exportar PDF" llama a
    `descargarPdf` con el título, los filtros y las filas esperadas (módulo `pdf` mockeado).
- Verificación completa del frontend (`format:check`, `lint`, `typecheck`, `test:coverage` ≥ 80 %,
  `build`) y la batería del backend (sin cambios de backend, se corre igual).
- Manual (opcional): abrir el PDF descargado y ver que se lee prolijo (título, filtros, fecha, tabla).

## Registro de gates

- Gate 1 (plan): 2026-10-22 — aprobado (con jsPDF + jspdf-autotable; botón junto al de CSV).
- Gate 2 (verificación): 2026-10-22 — Frontend: `format:check`, `lint`, `typecheck` en verde;
  `test:coverage` 100 pasan (líneas 89.65 %, sentencias 86.37 %, umbral 80 %); `build` ok (advertencia
  de tamaño de chunk por jsPDF, no error). Backend sin cambios: `ruff`, `mypy` (89), `makemigrations
  --check`, `pytest` (264) y gitleaks en verde.
- Gate 3 (PR): 2026-10-22 — PR #45 mergeado a `develop` (rama `feature/frontend-exportar-pdf`).
  Con esta unidad HU-052 queda completa.
