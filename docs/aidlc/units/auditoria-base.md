# Unidad: Auditoría de cambios — base y captura de reservas

- **Estado:** en curso · **Épica:** E1 Seguridad y acceso · **App dueña:** `auditoria` (+ `reservas`)
- **Origen:** HU-007 · **Rama:** `feature/auditoria-base`

## Objetivo

Dejar un **registro inmutable** de quién cambió qué y cuándo, y poder **consultarlo como un registro
general filtrable por usuario y fecha** (lo que gerencia necesita para investigar "yo nunca cambié esa
fecha", HU-007). Esta unidad arma la app `auditoria`, su servicio y el endpoint de lectura, y **captura
los cambios de Reserva** (el riesgo dominante del sistema). Campaña, tarifa de cartel y configuración, y
la **pantalla** del registro, van en unidades siguientes.

## Decisiones de diseño (mi criterio — corregir acá si hace falta)

1. **App nueva `auditoria`** (prevista en la arquitectura). Expone un **servicio** `registrar_cambios(...)`
   que las demás apps llaman para escribir (la arquitectura dice "las demás le escriben por su
   servicio"): por eso `reservas` importa `auditoria.services`, que es la excepción sancionada a la
   tabla de imports. `auditoria` no importa modelos de otras apps.
2. **Modelo `RegistroAuditoria`** (una fila por campo cambiado): `entidad` (p. ej. "reserva"),
   `entidad_id`, `campo`, `valor_anterior` (texto, nullable), `valor_nuevo` (texto, nullable),
   `usuario` (FK a User, `PROTECT`, nullable para origen sistema/importación), `origen`
   (`usuario`/`sistema`/`importacion`), `momento` (`auto_now_add`, indexado). `ordering = ["-momento"]`.
3. **Inmutable:** `save()` del modelo **rechaza updates** (solo permite insertar; si ya tiene `pk`,
   levanta error). El endpoint es **solo lectura** (sin create/update/delete en la API). No se registra
   en el admin con permiso de borrado. Así, cualquier rol que intente modificar un registro es
   rechazado (HU-007, criterio 3).
4. **Captura de Reserva:** en `ReservaViewSet.perform_update`, se toman los valores **anteriores** de
   los campos auditados antes de `serializer.save()` y los **nuevos** después, y se llama a
   `registrar_cambios` con `request.user`. Campos auditados: `fecha_inicio`, `fecha_fin`, `estado`,
   `cartel` (por `cartel_id`), `precio_alquiler`, `precio_impresion`, `precio_fijacion`. Solo se
   registran los que efectivamente cambiaron. La creación de una reserva no se audita en esta unidad
   (HU-007 habla de cambios con valor anterior y nuevo).
5. **Permiso de lectura:** solo **Gerencia** o superusuario (la auditoría es consulta de gerencia).
   Se reutiliza `LecturaSoloGerencia`.
6. **Endpoint** `GET /api/auditoria/registros/` con filtros opcionales `entidad`, `entidad_id`,
   `usuario` (id) y rango `desde`/`hasta` (fecha de `momento`, `AAAA-MM-DD`). Devuelve los registros
   ordenados del más nuevo al más viejo, con `usuario_nombre` resuelto.

## Cambios

- **App `backend/apps/auditoria/`** nueva: `__init__.py`, `apps.py`, `models.py` (`RegistroAuditoria`),
  `services.py` (`registrar_cambios`), `views.py` (`RegistrosView` solo lectura, Gerencia),
  `urls.py`, `migrations/` (0001 del modelo).
- `backend/config/settings.py`: `"apps.auditoria"` en `INSTALLED_APPS`.
- `backend/config/urls.py`: `path("api/auditoria/", include("apps.auditoria.urls"))`.
- `backend/apps/reservas/views.py`: en `ReservaViewSet`, capturar anteriores/nuevos de los campos
  auditados y llamar a `auditoria.services.registrar_cambios(...)` con el usuario. Mantener la
  transacción existente (la auditoría se escribe dentro de la misma `transaction.atomic`).

### `registrar_cambios` (firma)

`registrar_cambios(entidad: str, entidad_id: int, anteriores: dict[str, str], nuevos: dict[str, str],
usuario, origen="usuario") -> None`: crea un `RegistroAuditoria` por cada campo cuyo valor cambió
(compara `anteriores[campo]` vs `nuevos[campo]`, ambos ya como texto). `usuario` puede ser `None`.

## Reglas que se usan

- Ninguna del catálogo RN. Implementa HU-007 (criterios 1 parcial —registro consultable—, 2 —origen— y
  3 —inmutabilidad—). El criterio 1 completo (historial por registro en pantalla) y la cobertura de
  campaña/tarifa/config quedan para unidades siguientes.

## Migraciones

- `auditoria/0001_initial` (modelo `RegistroAuditoria`). `makemigrations --check` debe quedar limpio.

## Cómo se prueba

- Backend (`backend/tests/test_auditoria.py`, PostgreSQL real):
  - al editar una reserva (p. ej. cambiar `fecha_fin` y `estado`), quedan registros con usuario,
    momento, valor anterior y nuevo, solo de los campos que cambiaron (HU-007, criterio 1).
  - `registrar_cambios` no crea filas si nada cambió.
  - el modelo **rechaza un update** (guardar un `RegistroAuditoria` ya existente levanta error) y la API
    **no permite** PATCH/DELETE del registro (405) (criterio 3).
  - el endpoint filtra por `entidad`, `entidad_id`, `usuario` y rango de fechas; ordena del más nuevo
    al más viejo.
  - permisos: Gerencia/superusuario leen (200); Operativo y anónimo no (403 / 401-403).
- Verificación completa del backend (DoD). Sin cambios de frontend en esta unidad.

## Registro de gates

- Gate 1 (plan): 2026-10-22 — aprobado (solo Reserva; no se audita la creación; registro general
  filtrable; solo Gerencia). Implementación por subagente en Sonnet; revisión en Opus.
- Gate 2 (verificación): 2026-10-22 — Backend: `ruff`, `mypy` (98 archivos), `makemigrations --check`,
  gitleaks y `pytest --cov` 294 pasan, cobertura 94.80 %. Sin cambios de frontend. En revisión se
  envolvió el cambio de la reserva y su auditoría en una sola `transaction.atomic()` (atomicidad:
  nunca un cambio sin su registro), ya que `ATOMIC_REQUESTS` no está activado.
- Gate 3 (PR): —
