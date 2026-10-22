# Unidad: Reporte por rubro (ingresos y ocupación)

- **Estado:** en curso · **Épica:** E8 Reportes y paneles · **App dueña:** `facturacion` (+ `frontend`)
- **Origen:** HU-050 (solo la parte de rubro; grupo económico queda fuera) · **Rama:** `feature/facturacion-reporte-por-rubro`

## Objetivo

Que gerencia corte **ingresos** y **ocupación** por **rubro de la marca**, para saber qué industrias
dejan más plata y cuáles ocupan más carteles (HU-050, criterio 1). El rubro se toma de la **marca**,
nunca del cliente (que suele ser una agencia). El **grupo económico** (criterio 2) queda fuera: depende
de la pregunta 16, sin definir.

## Decisiones de diseño (mi criterio — corregir acá si hace falta)

1. **App `facturacion`:** el corte cruza reserva → campaña → marca → rubro, y es la única app que puede
   importar `reservas` + `campanias` + `clientes` (donde viven `Marca` y `Rubro`). Además incluye plata.
2. **Un endpoint** `GET /api/facturacion/por-rubro/?desde=AAAA-MM&hasta=AAAA-MM` que por cada rubro
   trae:
   - **ingresos** del período: suma del reparto por mes (HU-051) de las reservas que ocupan cupo,
     atribuidas al rubro de su marca; respeta el período (como el reporte de ingresos).
   - **días‑cupo ocupados**: suma de los días que esas reservas ocupan dentro del período (una reserva
     = un cupo, RN-004); y el **% sobre el total ocupado** del período.
   - Reservas cuya marca no tiene rubro (o sin marca) caen en un bucket **"Sin rubro"**.
   - Ordenado por **ingresos** descendente (ranking de industrias por plata).
3. **Permiso:** solo **Gerencia** (reusa `LecturaSoloGerencia`), porque muestra facturación. La pantalla
   se oculta a quien no es Gerencia, como la de Ingresos.
4. **Pantalla nueva** "Por rubro" bajo la sección **Reportes** (ítem `soloGerencia`), con filtro de
   período y una tabla `Rubro · Ingresos · Días‑cupo · % ocupación`. Export **CSV** y **PDF** reusando
   `shared/csv.ts` y `shared/pdf.ts`.
5. **Ocupación como días‑cupo + %**, no como % contra capacidad: la pregunta es "qué industrias ocupan
   más", o sea el reparto del espacio ocupado entre rubros (mi decisión; se puede cambiar).

## Cambios

- **Backend** (`backend/apps/facturacion/`):
  - `services.py`: `reporte_por_rubro(desde, hasta)` → agrega ingresos (reparto) y días‑cupo por rubro;
    devuelve `{ rubros: [{rubro, nombre, ingresos, dias_cupo, porcentaje_ocupacion}], total_ingresos,
    total_dias_cupo }`. Reusa `reservas.services.reparto_por_mes`.
  - `views.py` + `urls.py`: `PorRubroView` (solo lectura, Gerencia) en `GET /api/facturacion/por-rubro/`,
    parámetros `desde`/`hasta` en `AAAA-MM` (por defecto el año actual); valida formato y `desde ≤
    hasta` → 400.
- **Frontend** (`frontend/src/features/facturacion/`):
  - `PorRubro.tsx`: pantalla con filtro de período, tabla con ranking por ingresos y botones Exportar
    CSV/PDF.
  - `App.tsx`: ítem "Por rubro" en la sección Reportes, `soloGerencia: true`.
  - Tipos y (si hace falta) un pequeño helper de formato reusando `montos.ts`/`ocupacion.ts`.

## Reglas

- **HU-050 (parcial: rubro).** Criterio 1 cumplido (corte por rubro de la marca). Criterio 2 (grupo
  económico) fuera de alcance.
- **RN-004** se consume para los días‑cupo (una reserva = un cupo); no se reubica.

## Migraciones

Ninguna.

## Cómo se prueba

- Backend (`backend/tests/test_reporte_por_rubro.py`, PostgreSQL real):
  - una campaña de una agencia para una marca de Gastronomía corta por **Gastronomía**, no por la
    agencia (criterio 1).
  - ingresos por rubro cuadran contra la suma manual; días‑cupo por rubro cuadran; el `%` de ocupación
    suma 100 entre rubros con ocupación.
  - reservas sin rubro caen en "Sin rubro"; cancelada no cuenta; `desde > hasta`/formato inválido →
    400; **Operativo recibe 403** y anónimo 401/403 (dato de facturación).
- Frontend: la pantalla muestra el ranking por ingresos; los botones CSV/PDF disparan la descarga; el
  ítem "Por rubro" aparece solo para Gerencia.
- Verificación completa de backend y frontend (DoD).

## Registro de gates

- Gate 1 (plan): 2026-10-22 — aprobado (ambas métricas por rubro; ocupación en días-cupo + %; solo
  Gerencia; grupo económico fuera). Implementación por subagente en Sonnet; revisión en Opus.
- Gate 2 (verificación): 2026-10-22 — Backend: `ruff`, `mypy` (90 archivos), `makemigrations --check`,
  gitleaks y `pytest --cov` 275 pasan (11 nuevos), cobertura 94.69 %. Frontend: `format:check`, `lint`,
  `typecheck`, `test:coverage` 106 pasan (líneas 89.37 %) y `build` OK. En revisión se reemplazó el
  import de la función privada `_dias_solape` por una copia local en `facturacion`.
- Gate 3 (PR): —
