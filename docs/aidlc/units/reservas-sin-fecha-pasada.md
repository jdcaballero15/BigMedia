# Unidad: reservas-sin-fecha-pasada

- **Estado:** en revisión · **Épica:** E5 Reservas y motor de disponibilidad · **App dueña:** reservas
- **Origen:** RN-012 · **Rama:** `feature/reservas-sin-fecha-pasada`
- **Depende de:** el PR #117 (respuesta de RN-012), que tiene que estar mergeado antes del PR de
  código.

## Objetivo

Que no se pueda cargar a mano una reserva que ya terminó (RN-012). La regla es provisoria, así que
se puede apagar desde Parámetros.

## Encuadre

- **RN-012 (`provisoria`, Gonza 2026-11-04):** no hay histórico para importar y un operativo no
  puede crear a mano una reserva con fecha pasada. Hoy el servidor la acepta.
- **Decisiones de Gonza (2026-11-04):**
  - Cuenta como fecha pasada la reserva que **termina antes de hoy** (`fecha_fin < hoy`). Una que
    empezó hace unos días y sigue al aire se puede registrar con su inicio real.
  - Es **configurable**: interruptor «Permitir reservas con fecha pasada» en Parámetros, apagado
    por defecto, como RN-001 y RN-002.
- **App dueña:** `reservas`. Sin dependencias nuevas entre apps.
- **Capas:** backend (modelo, servicio, serializers, vista) y frontend (pantalla Parámetros).

## Cambios

- **Modelo:** `ParametrosDisponibilidad.permitir_fecha_pasada`, `BooleanField(default=False)`.
- **Servicio** `validar_fecha_no_pasada(fecha_fin)` en `apps/reservas/services.py`: si el parámetro
  está apagado y `fecha_fin < hoy`, error en `fecha_fin`: «La reserva termina antes de hoy: no se
  puede cargar con fecha pasada.». «Hoy» es `timezone.localdate()`, a través de una función
  `hoy()` del mismo módulo.
- **Dónde se valida:**
  - Alta suelta (`ReservaSerializer`): siempre.
  - Edición: solo si cambia `fecha_fin`. Una reserva vieja se puede seguir editando en lo demás
    (estado, precio, cancelarla).
  - Creación en bloque (`ReservasEnBloqueSerializer`): la tanda entera se rechaza con 400.
  - `mover-pendientes`: si la campaña quedó con un fin anterior a hoy, no se mueve nada y da error.
- **Parámetros:** `permitir_fecha_pasada` en `ParametrosDisponibilidadSerializer` y un interruptor
  más en `ParametrosPage`, con su explicación, como los dos que ya hay.
- **Docs:** columna «Dónde vive» de RN-012 y el manual (Parámetros y la tabla de mensajes).

## Fuera de alcance

- Limitar las fechas en el selector del formulario de reserva (el mensaje del servidor alcanza).
- Las fechas de la campaña: la regla es sobre reservas.
- Reservas creadas fuera de la API (datos de ejemplo, admin).

## Migraciones

`reservas.00xx_parametros_fecha_pasada`: agrega la columna con default `False`. Aditiva, sin mover
datos.

## Tests y fechas fijas

Hay 14 archivos de test que crean reservas por la API con fechas fijas de 2026, varias ya pasadas.
Para que no se rompan hoy ni a medida que pasen los días, un fixture `autouse` en
`backend/tests/conftest.py` fija `services.hoy()` en el 2026-01-01, antes de todas esas fechas. Los
tests de RN-012 fijan su propio «hoy». No se apaga la regla en los tests: se fija la fecha.

## Reglas provisorias que se usan

- RN-012: no se carga a mano una reserva con fecha pasada (fin anterior a hoy), configurable.

## Cómo se prueba

`backend/tests/test_reservas_fecha_pasada.py`, contra PostgreSQL, con
`@pytest.mark.regla("RN-012")`:

- alta con fin anterior a hoy → 400 en `fecha_fin`; con fin hoy o después (aunque empiece antes) →
  201;
- edición que lleva el fin a antes de hoy → 400; edición de otro campo de una reserva ya terminada
  → 200;
- creación en bloque con fin anterior a hoy → 400 y ninguna reserva creada;
- `mover-pendientes` con la campaña terminada antes de hoy → 400 y nada movido;
- con el parámetro prendido, las cuatro anteriores se permiten;
- `GET`/`PATCH` de parámetros incluye `permitir_fecha_pasada`.

Frontend: `ParametrosPage.test.tsx` cubre el interruptor nuevo.

## Registro de gates

- Gate 1 (plan): 2026-11-04 — aprobado por Gonza
- Gate 2 (verificación): 2026-11-04 — `ruff format --check` y `ruff check` sin errores; `mypy backend`
  sin errores (146 archivos); `makemigrations --check` sin cambios (migración `reservas.0005`
  revisada a mano: un `AddField` booleano); `pytest --cov` 918 passed, 97,27 %; frontend:
  `format:check`, `lint`, `typecheck`, `test:coverage` (395 tests, 92,75 % de sentencias, 94,77 % de
  líneas) y `build` en verde; `pre-commit run --all-files` en verde, gitleaks incluido.
- Gate 3 (PR): #118
