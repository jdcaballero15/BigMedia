# Unidad: Pantalla del reporte de ocupación

- **Estado:** en curso · **Épica:** E8 Reportes y paneles · **App dueña:** `frontend`
- **Origen:** HU-048 (pantalla) · **Rama:** `feature/frontend-reporte-ocupacion`

## Objetivo

Darle a gerencia la pantalla de ocupación, consumiendo `GET /api/reservas/reporte-ocupacion/`, con las
tres vistas del HU-048: ranking de carteles, evolución mensual y mapa de calor cartel × mes. Cierra la
parte visible de HU-048 (el backend ya está mergeado).

## Decisiones de diseño (mi recomendación — corregir acá si hace falta)

1. **Las tres vistas en una sola pantalla**, sin librería de gráficos (el endpoint ya trae todo):
   - **Mapa de calor cartel × mes:** tabla con una fila por cartel y una columna por mes; cada celda
     muestra el % y se colorea según la ocupación (más intenso = más ocupado). Como el backend ya
     ordena los carteles por ocupación del período, **la misma tabla es el ranking** (arriba, los de
     mejor rendimiento); la primera columna muestra el cartel y su % total.
   - **Evolución por modalidad:** tabla compacta aparte (una fila por modalidad, una columna por mes +
     total), que no mezcla fijos con digitales.
2. **Color del calor:** helper `colorOcupacion(pct)` que devuelve un fondo con opacidad proporcional al
   % sobre el color de acento (no hace falta agregar clases nuevas al CSS).
3. **Filtros:** período `Desde`/`Hasta` (`input month`, por defecto el año actual), `Zona` (de
   `/api/inventario/zonas/`) y `Modalidad` (fija/digital). Al cambiar cualquiera, se vuelve a pedir.
4. **Formato del %:** 1 decimal con `%` (es-AR), helper `formatearPorcentaje`.
5. **Dónde vive:** feature `frontend/src/features/reservas/`, calcando el patrón de
   `CalendarioDisponibilidad` (grilla cartel × mes, filtros, estados de carga/vacío/error).
6. **Navegación:** se agrega el ítem **"Ocupación"** a la sección "Reportes" de la barra lateral
   (`App.tsx`), junto a "Ingresos".
7. **Visibilidad:** aparece para cualquier usuario con sesión (como las demás vistas de reservas).

## Cambios

- `frontend/src/features/reservas/reporteOcupacion.ts` (o `types.ts`): tipos `ReporteOcupacion`,
  `CartelOcupacion`, `CeldaOcupacion`, `ModalidadOcupacion`, `PeriodoOcupacion`; helpers
  `formatearPorcentaje` y `colorOcupacion`.
- `frontend/src/features/reservas/ReporteOcupacion.tsx`: la pantalla (filtros + tabla de evolución por
  modalidad + mapa de calor/ranking).
- `frontend/src/features/reservas/ReporteOcupacion.test.tsx`: tests con `fetch` mockeado.
- `frontend/src/App.tsx`: ítem "Ocupación" en la sección "Reportes".

## Reglas

Ninguna nueva. La pantalla solo muestra lo que el backend ya calcula (ocupación en días-cupo, RN-004).

## Migraciones

Ninguna.

## Cómo se prueba

- Frontend (`ReporteOcupacion.test.tsx`, Vitest + Testing Library, `fetch` mockeado para
  `/reservas/reporte-ocupacion/` y `/inventario/zonas/`):
  - el mapa de calor muestra los carteles (en el orden del backend = ranking) con las columnas de meses
    y el % de cada celda.
  - la tabla de evolución muestra los totales por modalidad.
  - al cambiar el período (o zona/modalidad), vuelve a pedir el reporte con los nuevos parámetros.
  - estado vacío cuando no hay carteles; alerta ante error.
- Verificación completa del frontend (`format:check`, `lint`, `typecheck`, `test:coverage` ≥ 80 %,
  `build`) y la batería del backend (sin cambios de backend, pero se corre igual).

## Registro de gates

- Gate 1 (plan): 2026-10-21 — aprobado (tres vistas en una pantalla; mapa de calor coloreado por %;
  evolución por modalidad como tabla; sección "Reportes").
- Gate 2 (verificación): 2026-10-21 — Frontend: `format:check`, `lint`, `typecheck` en verde;
  `test:coverage` 89 pasan (cobertura líneas 89 %, sentencias 86 %, umbral 80 %); `build` ok.
  Backend sin cambios: `ruff`, `makemigrations --check`, `pytest` (257 pasan) y gitleaks en verde.
- Gate 3 (PR): —
