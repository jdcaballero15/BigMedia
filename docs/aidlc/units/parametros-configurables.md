# Unidad: Parámetros configurables

- **Estado:** en revisión · **Épica:** E0 Plataforma base · **App dueña:** `reservas`
  (+ `config`, `auditoria`, `frontend`)
- **Origen:** HU-001 (RN-001, RN-002) · **Rama:** `feature/reservas-parametros-configurables`

## Objetivo

Que el administrador cambie desde la aplicación si el día de borde es inclusivo (RN-001) y si la
reserva tentativa cuenta para el bloqueo duro (RN-002). La validación de disponibilidad usa el
valor nuevo de inmediato, y cada cambio queda auditado (HU-001, criterios 1 a 3).

## Punto de partida (relevamiento del 23/10/2026)

- Los dos parámetros ya existen, pero como variables de entorno leídas al arrancar
  (`backend/config/settings.py`): `DISPONIBILIDAD_BORDE_INCLUSIVO` (por defecto `true`) y
  `DISPONIBILIDAD_TENTATIVA_BLOQUEA` (por defecto `false`). Para cambiarlas hay que redesplegar:
  hoy no se cumple el criterio 1.
- No están en `backend/.env.example` ni en `render.yaml`, así que en todos los entornos rigen los
  valores por defecto.
- Se leen en un solo lugar, `apps/reservas/services.py`: `_fin_efectivo` (RN-001) y
  `_estados_que_bloquean` (RN-002). Los usan la validación dura (`validar_disponibilidad`) y el
  calendario (`_pico_en_rango`).
- `test_disponibilidad.py` los cambia con `override_settings`.
- El rol Administrador y el permiso `SoloAdministrador` ya existen (`gestion-de-usuarios`), y
  `auditoria.services.registrar_cambios` ya sirve para el criterio 3.
- En la navegación ya hay una sección "Configuración" con "Catálogos".
- La unidad `baja-logica` (PR #66) todavía no está mergeada. Esta rama sale del `develop` actual, así
  que al mergear la segunda va a haber un conflicto chico en `units.md` y en el roadmap.

## Preguntas al equipo

Respondidas por Gonza el 23/10/2026: se aceptan las opciones recomendadas o propuestas.


1. **Dónde viven los parámetros.** La arquitectura no tiene una app de configuración, y `CLAUDE.md`
   §8 prohíbe crear apps que no estén en la tabla.
   - a) **Un modelo de una sola fila en `reservas`** (`ParametrosDisponibilidad`): son reglas del
     motor de disponibilidad, que es de `reservas`, y no hace falta una app nueva. **(recomendado)**
   - b) **Una app nueva `configuracion`**, pensada para futuros parámetros. Exige antes un ADR y
     actualizar la tabla de apps de `CLAUDE.md` y `docs/arquitectura.md`.
2. **Las variables de entorno.**
   - a) **Se eliminan.** Una migración de datos crea la fila con los valores actuales (borde
     inclusivo, tentativa sin bloqueo duro), y desde ahí la única fuente es la base. **(recomendado)**
   - b) Se conservan como valor inicial de la fila. Así se puede arrancar un entorno con otros
     valores, pero hay dos lugares donde mirar.
3. **La pantalla.** Propuesta: un ítem "Parámetros" en la sección Configuración, visible solo para
   el rol Administrador. Muestra los dos parámetros como casillas, cada una con una explicación de
   una línea y un ejemplo ("si una reserva termina el 15 y otra empieza el 15, se pisan"). ¿Está bien?
4. **Valores iniciales en producción.** RN-001 y RN-002 siguen `provisoria`, a la espera de Seba.
   Propuesta: arrancar con los valores de hoy (borde inclusivo y tentativa sin bloqueo duro). ¿Está
   bien, o ya hay respuesta de Seba?

## Respuestas

1. Un modelo de una sola fila en `reservas`; no hay app nueva.
2. Las variables de entorno se eliminan; una migración de datos crea la fila.
3. Ítem "Parámetros" en Configuración, solo para el rol Administrador.
4. Valores iniciales: borde inclusivo y tentativa sin bloqueo duro.

## Decisiones de diseño (mi criterio — corregir acá si hace falta)

5. **Sin caché:** el servicio lee la fila en cada validación. Es una consulta por cada confirmación,
   y así el cambio rige al instante, sin reiniciar nada (criterio 1).
6. **Lectura dentro de la transacción:** `validar_disponibilidad` lee el parámetro dentro de la
   misma transacción que ya bloqueó el cartel. Si alguien cambia el parámetro mientras otro confirma,
   esa confirmación usa el valor que estaba vigente al empezar.
7. **Una sola fila:** el modelo fuerza `pk=1` y no se puede borrar. La API es
   `GET/PATCH /api/reservas/parametros/`, con `SoloAdministrador` y sin `POST` ni `DELETE`.
8. **Auditoría:** `registrar_cambios` con la entidad `parametros`, un campo por parámetro. Se suma a
   las etiquetas y al filtro de la pantalla de Auditoría.
9. **Cambiar un parámetro no recalcula las reservas que ya existen.** Rige para las validaciones
   siguientes; si eso deja una sobreventa, no se corrige sola. La pantalla lo advierte.

## Cambios

- `backend/apps/reservas/models.py`: `ParametrosDisponibilidad` (`borde_inclusivo`,
  `tentativa_bloquea`) y su migración de esquema más una de datos con la fila inicial.
- `backend/apps/reservas/services.py`: `parametros_disponibilidad()`; `_fin_efectivo` y
  `_estados_que_bloquean` leen de ahí.
- `backend/apps/reservas/serializers.py`, `views.py` y `urls.py`: la API de parámetros, con
  auditoría.
- `backend/config/settings.py`: se eliminan las dos variables (pregunta 2).
- `backend/tests/test_disponibilidad.py`: cambiar `override_settings` por la fila de parámetros.
- `frontend/src/features/reservas/ParametrosPage.tsx` (nuevo) y su test.
- `frontend/src/App.tsx`: ítem "Parámetros" en Configuración, `soloAdministrador`.
- `frontend/src/features/auditoria/Auditoria.tsx`: la entidad `parametros`.
- `docs/aidlc/reglas-de-negocio.md`: solo la columna "Dónde vive" de RN-001 y RN-002.

## Migraciones

Dos en `reservas`: una de esquema (tabla nueva) y una de datos (la fila inicial). Ninguna toca
datos existentes.

## Reglas provisorias que se usan

- RN-001 (`provisoria`): día de borde inclusivo, el día compartido se pisa.
- RN-002 (`provisoria`): la tentativa ocupa cupo solo visualmente; el bloqueo duro es al confirmar.

## Cómo se prueba

- `test_parametros_cambio_de_borde_rige_en_la_siguiente_validacion` (criterio 1,
  `@pytest.mark.regla("RN-001")`).
- `test_parametros_tentativa_bloquea_rige_en_la_siguiente_validacion` (criterio 1,
  `@pytest.mark.regla("RN-002")`).
- `test_parametros_no_administrador_no_accede` (criterio 2: Operativo, Lectura y Gerencia, en `GET` y
  en `PATCH`).
- `test_parametros_cambio_queda_auditado_con_usuario` (criterio 3).
- `test_parametros_fila_inicial_tiene_los_valores_provisorios`.
- `test_parametros_post_y_delete_devuelven_405`.
- Los tests de `test_disponibilidad.py` que hoy usan `override_settings`, ahora con la fila.
- Frontend: `ParametrosPage` carga, guarda y muestra el error del servidor; el ítem no aparece para
  quien no es Administrador.

## Registro de gates

- Gate 1 (plan): 23/10/2026 — aprobado por Gonza
- Gate 2 (verificación): corrida el 26/10/2026 — backend 400 tests, 95,56 %; frontend 163 tests; aprobado por Gonza el 26/10/2026
- Gate 3 (PR): —
