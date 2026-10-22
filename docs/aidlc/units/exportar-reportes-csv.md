# Unidad: Exportar reportes a CSV

- **Estado:** mergeada · **Épica:** E8 Reportes y paneles · **App dueña:** `frontend`
- **Origen:** HU-052 (parcial: CSV) · **Rama:** `feature/frontend-exportar-reportes`

## Objetivo

Permitir que gerencia exporte a CSV los reportes de **Ingresos** y **Ocupación** para trabajarlos en
Excel, respetando los filtros aplicados (HU-052, criterio 1). El PDF y el rechazo por permiso quedan
fuera de esta unidad (ver "Fuera de alcance").

## Decisiones de diseño (mi criterio — corregir acá si hace falta)

1. **CSV del lado del cliente**, armado desde los datos que la pantalla ya tiene cargados (con los
   filtros puestos). Así "el CSV contiene exactamente las filas visibles" sale solo y no hace falta
   backend.
2. **Formato para Excel argentino:** separador `;`, decimales con coma, campos de texto entre comillas
   (y comillas internas escapadas), y UTF-8 con BOM para que los acentos se vean bien al abrir en
   Excel. Los importes/porcentajes van como número (sin `$` ni `%`), para que Excel los trate como
   números.
3. **Alcance:** un botón "Exportar CSV" en los dos reportes con filtros, **Ingresos** y **Ocupación**.
   Otras listas (clientes, carteles) quedan para más adelante.
4. **Separación de responsabilidades:** una función pura `construirCsv(columnas, filas)` (testeable sin
   DOM) y un `descargarCsv(nombreArchivo, columnas, filas)` que agrega el efecto de descarga (Blob +
   enlace). Helper compartido en `frontend/src/shared/csv.ts`.
5. **Nombre de archivo:** `<reporte>-<desde>-<hasta>.csv` (p. ej. `ingresos-2026-01-2026-12.csv`).
6. **Qué columnas:**
   - Ingresos: una fila por marca, con columnas `Cliente`, `Marca`, una por mes del período y `Total`.
     (Cada marca ya trae su cliente en la pantalla.)
   - Ocupación: una fila por cartel, con columnas `Cartel`, `Modalidad`, `Zona`, una por mes (%) y
     `Total`.

## Cambios

- `frontend/src/shared/csv.ts`: `construirCsv(columnas, filas)` y `descargarCsv(nombre, columnas, filas)`.
- `frontend/src/features/facturacion/ReporteIngresos.tsx`: botón "Exportar CSV" que aplana
  clientes → marcas a filas y descarga.
- `frontend/src/features/reservas/ReporteOcupacion.tsx`: botón "Exportar CSV" que arma las filas de los
  carteles y descarga.
- Tests: `frontend/src/shared/csv.test.ts` (función pura) y asserts en los tests de cada pantalla de
  que el botón existe y, al tocarlo, se dispara la descarga.

## Reglas

- **HU-052 (parcial).** Se cumple el criterio 1 (el CSV respeta los filtros y contiene las filas
  visibles). El criterio 2 (rechazo a usuarios sin permiso de ver ingresos) y el criterio 3 (PDF con
  título, filtros y fecha) quedan fuera de esta unidad.

## Fuera de alcance (HU-052 que queda abierto)

- **Exportar a PDF** (criterio 3).
- **Gate de permiso de facturación** (criterio 2), atado a la definición del permiso "ver ingresos"
  (grupo "Gerencia"), diferida.
- Exportar otras listas (clientes, carteles, campañas).

## Migraciones

Ninguna.

## Cómo se prueba

- Frontend:
  - `csv.test.ts`: `construirCsv` arma encabezados y filas con `;`, comилla el texto, usa coma decimal
    y escapa comillas; una celda con `;` o `"` se encierra bien.
  - `ReporteIngresos.test.tsx`: el botón "Exportar CSV" aparece y, al tocarlo, dispara la descarga
    (se espía `URL.createObjectURL`).
  - `ReporteOcupacion.test.tsx`: ídem para el reporte de ocupación.
- Verificación completa del frontend (`format:check`, `lint`, `typecheck`, `test:coverage` ≥ 80 %,
  `build`) y la batería del backend (sin cambios de backend, se corre igual).

## Registro de gates

- Gate 1 (plan): 2026-10-21 — aprobado (CSV cliente-side; separador `;`, coma decimal, BOM;
  botón en Ingresos y Ocupación; PDF y gate de permiso fuera de alcance).
- Gate 2 (verificación): 2026-10-21 — Frontend: `format:check`, `lint`, `typecheck` en verde;
  `test:coverage` 94 pasan (cobertura líneas 89 %, sentencias 86 %, umbral 80 %); `build` ok.
  Backend sin cambios: `ruff`, `makemigrations --check`, `pytest` (257 pasan) y gitleaks en verde.
- Gate 3 (PR): 2026-10-21 — PR #35 mergeado a `develop` (rama `feature/frontend-exportar-reportes`).
