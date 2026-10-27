# Unidad: Sobreventa por reservas Finalizadas

- **Estado:** en curso · **Épica:** E5 Reservas y motor de disponibilidad · **App dueña:** `reservas`
- **Origen:** hallazgo de la prueba manual de reservas (24/10/2026), reproducido el 26/10/2026 ·
  HU-031, HU-035 · **Rama:** `fix/reservas-sobreventa-finalizada`

## Objetivo

Que ninguna vía permita ocupar un cartel sin cupo. Hoy el control de cupo solo corre cuando una
reserva queda **Confirmada**, pero una **Finalizada** también ocupa el cupo. Por eso hay tres vías
por donde entra una sobreventa:

1. **Alta como Finalizada.** Reproducido el 26/10/2026 contra la base local, dentro de una
   transacción deshecha: en Ruta 7 km 1020, ocupado del 01/09 al 30/11/2026 por "Los Álamos", el
   alta como Confirmada devuelve 400 (sin cupo) y la misma alta como Finalizada devuelve **201**.
2. **Confirmada → Finalizada cambiando fechas o cartel** en la misma edición: no se revalida.
3. **Edición de una Finalizada** que cambia fechas o cartel: no se revalida.

HU-031 pide que la validación corra "de modo que ninguna vía de entrada pueda saltearla", y HU-035
que una transición inválida "se rechace por cualquier vía".

## Decisiones (Juan Diego, 26/10/2026)

1. **Una reserva nueva solo puede crearse Pendiente o Confirmada.** Crearla Finalizada o Cancelada
   se rechaza con "Una reserva nueva solo puede crearse Pendiente o Confirmada." Sigue el ciclo de
   vida de HU-035. Las reservas históricas como Finalizada entran por el importador de HU-038, que
   todavía no existe y tendrá su propia unidad.
2. **El cupo se controla siempre que la reserva termina ocupando de forma dura** (Confirmada o
   Finalizada) y además se da una de estas condiciones: es un alta, viene de un estado que no
   ocupaba de forma dura, o cambian las fechas o el cartel. Confirmada → Finalizada sin otros
   cambios no se revalida, porque el cupo ya estaba validado. Pendiente sigue sin validación dura
   (RN-002).

## Cambios

- `reservas/services.py`:
  - `validar_estado_inicial(estado)`: rechaza un alta que no sea Pendiente o Confirmada.
  - `necesita_validar_cupo(estado_anterior, estado_nuevo, cambia_ocupacion)`: la regla de la
    decisión 2. La lógica sale de la vista y queda en el servicio, donde van las reglas de negocio.
- `reservas/serializers.py`: en el alta llama a `validar_estado_inicial`.
- `reservas/views.py`: `perform_create` y `perform_update` usan `necesita_validar_cupo`. El bloqueo
  con `select_for_update` y la transacción no cambian.
- `frontend/src/features/reservas/ReservaForm.tsx`: en el alta, el selector de estado solo ofrece
  Pendiente y Confirmada. En la edición sigue mostrando los cuatro, porque las transiciones las
  controla el servidor.

## Migraciones

Ninguna.

## Reglas provisorias que se usan

- RN-002 (provisoria): Pendiente ocupa cupo solo visualmente; el bloqueo duro es al confirmar. No
  cambia: Finalizada ya contaba como ocupación dura y se mantiene.

No cambia el valor de ninguna regla, así que no hace falta un PR `docs/historias-…`.

## Cómo se prueba

En `backend/tests/test_reservas.py`, cada uno empieza fallando y reproduce el bug:

- `test_alta_finalizada_cartel_ocupado_se_rechaza`: alta como Finalizada → 400 por el estado.
- `test_alta_cancelada_se_rechaza`: alta como Cancelada → 400 por el estado.
- `test_alta_pendiente_y_confirmada_libres_se_permiten`: los dos estados válidos siguen andando.
- `test_confirmada_a_finalizada_moviendo_fechas_sobre_ocupado_se_rechaza`: 400 por cupo.
- `test_confirmada_a_finalizada_sin_cambios_no_revalida`: 200 aunque el cupo hoy esté lleno.
- `test_finalizada_cambia_cartel_a_ocupado_se_rechaza`: 400 por cupo.
- Tests unitarios de `necesita_validar_cupo` con la tabla de combinaciones.

En el frontend, `ReservaForm.test.tsx`: el alta ofrece solo Pendiente y Confirmada; la edición ofrece
los cuatro.

A mano en `localhost`: repetir el alta como Finalizada en Ruta 7 km 1020 y ver que ya no aparece la
opción. Con la API, que se rechace.

## Fuera de esta unidad

- Revisar si en staging o producción ya hay sobreventas cargadas por esta vía. Se puede hacer con una
  consulta de solo lectura si Gonza o Juan Diego lo piden.
- RN-010 (carteles en mantenimiento o apagados), RN-012 (fechas pasadas), el vencimiento de sesión y
  el formato del mensaje de conflicto: unidades aparte.

## Registro de gates

- Gate 1 (plan): 2026-10-26 — aprobado por Juan Diego (alta solo Pendiente o Confirmada)
- Gate 2 (verificación): 2026-10-26 — los 4 tests del bug fallaron antes del arreglo (201/200 en
  vez de 400). Backend: `ruff format --check` y `ruff check` ok, `mypy` sin errores en 116
  archivos, `makemigrations --check` sin cambios, `pytest --cov` 513 en verde (96,05 %). Frontend:
  `format:check` ok, `lint` y `typecheck` sin errores, `test:coverage` 182 en verde (sentencias
  87,92 %, líneas 91,01 %), `build` ok. `pre-commit run --all-files` en verde, gitleaks incluido.
  Falta la prueba a mano en `localhost`.
- Gate 3 (PR): pendiente
