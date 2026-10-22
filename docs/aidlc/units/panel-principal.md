# Unidad: Panel principal

- **Estado:** en curso · **Épica:** E8 Reportes y paneles · **App dueña:** `reservas`
- **Origen:** HU-047 · **Rama:** `feature/reservas-panel-principal`

## Objetivo

Un panel de inicio que muestre de un vistazo el estado del negocio: carteles libres y ocupados hoy,
campañas activas (confirmadas) y reservas por vencer. Reusa lo ya hecho; no crea apps nuevas.

## Cambios

- `reservas/services.py` + `views.py` + `urls.py`: endpoint de solo lectura `GET /api/reservas/panel/`
  → `{ carteles_libres, carteles_ocupados, campanias_activas, por_vencer: [...] }`. `reservas` ya
  importa `campanias` e `inventario`, así que agrega todo en una vista.
- `config/settings.py`: `PANEL_DIAS_POR_VENCER` (default 30), configurable por entorno.
- Frontend `frontend/src/features/panel/PanelPrincipal.tsx`: tarjetas con los contadores y la lista de
  reservas por vencer. Entrada de navegación "Panel".

### Reglas (HU-047)

- `carteles_libres` / `carteles_ocupados`: carteles no de baja, según la ocupación de hoy (HU-040):
  ocupado si los cupos vigentes alcanzan la capacidad; libre si no.
- `campanias_activas`: campañas en estado `confirmada`, sin filtrar por fecha (RN de HU-024).
- `por_vencer`: reservas `confirmada` cuya `fecha_fin` cae entre hoy y hoy + `PANEL_DIAS_POR_VENCER`
  días; cada una con datos para abrir su ficha (id, nombre, cartel, fechas, campaña).

## Migraciones

Ninguna.

## Reglas que se usan

- Reusa la ocupación de hoy (HU-040) y el estado de campaña confirmada (HU-024). Sin cambios de reglas.

## Cómo se prueba

- Backend (`backend/tests/test_panel.py`): cuenta libres/ocupados excluyendo bajas; cuenta campañas
  confirmadas (no cotizadas/canceladas); lista las reservas confirmadas que vencen dentro de la ventana
  y excluye las que vencen después o no están confirmadas; anónimo → 401/403.
- Frontend (Vitest): `PanelPrincipal` muestra los contadores y la lista de por vencer.

## Registro de gates

- Gate 1 (plan): 2026-10-20 — aprobado por Juan Diego.
- Gate 2 (verificación): 2026-10-20 — ruff y mypy (79 archivos) OK, makemigrations --check sin cambios, pytest --cov 233 pasan (total 94.5%); frontend format/lint/typecheck OK, test:coverage 81 pasan, build OK; pre-commit en verde. Aprobado por Juan Diego.
- Gate 3 (PR): —
