# Unidad: Auditoría — estado de campaña y tarifa de cartel

- **Estado:** mergeada · **Épica:** E1 Seguridad y acceso · **App dueña:** `campanias`, `inventario` (+ `frontend`)
- **Origen:** HU-007 (extender captura) · **Rama:** `feature/auditoria-campania-cartel`

## Objetivo

Completar la captura de auditoría de HU-007 más allá de las reservas: registrar los **cambios de
estado de una campaña** y los **cambios de tarifa de lista de un cartel**, con el mismo registro
inmutable y la misma pantalla ya existentes.

## Decisiones de diseño (mi criterio — corregir acá si hace falta)

1. **Qué se audita:** `Campania.estado` (entidad `"campania"`) y `Cartel.tarifa_lista` (entidad
   `"cartel"`), que son los campos que lista HU-007 para esas entidades.
2. **Configuración queda afuera:** HU-007 también menciona cambios de configuración, pero los
   parámetros hoy son variables de entorno (no hay API editable); se auditarán cuando exista la
   configuración por pantalla (HU-001). Se deja anotado.
3. **Mismo patrón que reservas:** override de `perform_update` en `CampaniaViewSet` y `CartelViewSet`
   que toma el valor anterior del campo antes de `serializer.save()` y el nuevo después, y llama a
   `auditoria.services.registrar_cambios(...)` con `request.user` **dentro de una
   `transaction.atomic()`** (el cambio y su auditoría, todo o nada). Que estas apps importen
   `auditoria.services` es la excepción sancionada por la arquitectura.
4. **Solo updates**, no la creación (HU-007 habla de valor anterior y nuevo). Solo se registra si el
   campo efectivamente cambió (lo garantiza `registrar_cambios`).
5. **Frontend (chico):** en la pantalla de auditoría, agregar **"Campaña"** y **"Cartel"** al filtro de
   Entidad (values `campania` y `cartel`), y mostrar etiquetas lindas en la tabla
   (`campania` → "Campaña #5", `cartel` → "Cartel #5"; `reserva` → "Reserva #5").

## Cambios

- `backend/apps/campanias/views.py`: `perform_update` en `CampaniaViewSet` que audita `estado`.
- `backend/apps/inventario/views.py`: `perform_update` en `CartelViewSet` que audita `tarifa_lista`.
- `frontend/src/features/auditoria/Auditoria.tsx`: opciones "Campaña"/"Cartel" en el filtro de Entidad
  y un mapa de etiquetas para la columna Entidad.
- Tests: backend (editar estado de campaña y tarifa de cartel por la API genera registros;
  los campos que no cambian no se registran) y frontend (el filtro de Entidad incluye las nuevas
  opciones).

## Reglas

Ninguna nueva. Completa la cobertura de HU-007 para las entidades con edición por API. Configuración
queda pendiente de HU-001.

## Migraciones

Ninguna.

## Cómo se prueba

- Backend (`backend/tests/test_auditoria.py`, se agregan casos):
  - al cambiar el `estado` de una campaña por `PATCH`, queda un registro `entidad="campania"`,
    `campo="estado"`, con usuario, valor anterior y nuevo.
  - al cambiar la `tarifa_lista` de un cartel por `PATCH`, queda un registro `entidad="cartel"`,
    `campo="tarifa_lista"`.
  - editar otro campo que no se audita (o no cambiar nada) no genera registros de esa entidad.
- Frontend (`Auditoria.test.tsx`): el desplegable de Entidad ofrece "Campaña" y "Cartel"; la columna
  Entidad muestra la etiqueta correcta.
- Verificación completa de backend y frontend (DoD).

## Registro de gates

- Gate 1 (plan): 2026-10-22 — aprobado (estado de campaña + tarifa de cartel; config fuera, depende de
  HU-001). Implementación por subagente en Sonnet; revisión en Opus.
- Gate 2 (verificación): 2026-10-22 — Backend: `ruff`, `mypy` (98), `makemigrations --check`, gitleaks
  y `pytest --cov` 303 pasan (94.89 %). Frontend: `format:check`, `lint`, `typecheck`, `test:coverage`
  115 pasan y `build` OK. Revisión: ambos `perform_update` capturan el valor anterior antes de
  `save()` y auditan en la misma `transaction.atomic()`, sin pisar la validación existente; sin ajustes.
- Gate 3 (PR): 2026-10-22 — PR #53 mergeado a `develop` (rama `feature/auditoria-campania-cartel`).
  Con esto HU-007 queda completa salvo configuración (depende de HU-001).
