# Unidad: Ajuste del selector y el formato de fechas

- **Estado:** en curso · **Épica:** — (unidad técnica) · **App dueña:** `frontend`
- **Origen:** hallazgo de la prueba manual de reservas del 24/10/2026 (Juan Diego) · **Rama:** `fix/frontend-selector-de-fechas`

## Objetivo

Que todas las fechas del sistema se carguen y se lean como **dd/mm/aaaa**, con un calendario
desplegable en español. Hoy los campos usan el `<input type="date">` del navegador, que toma el
formato del idioma de Chrome (mes/día/año en inglés). En la prueba eso hizo cargar una reserva
desde el 11/01/2026 cuando se quería el 01/11/2026.

## Decisiones de diseño (aprobadas por Juan Diego, 24/10/2026)

1. **Librería `react-day-picker` 10.0.2** (publicada el 30/09/2026) para el calendario. Trae
   `date-fns` y `@date-fns/tz` como dependencias propias; el código de la app no las importa
   directo, así que no se agregan a `package.json`.
2. **Un solo componente `CampoFecha`** en `frontend/src/shared/`: campo de texto dd/mm/aaaa más un
   botón con ícono de calendario que despliega el mes. Se puede escribir o elegir. Semana de lunes a
   domingo, nombres en español. Se cierra al elegir un día, con Escape o al hacer clic afuera.
3. **La API no cambia:** el componente recibe y devuelve `aaaa-mm-dd`, el formato que ya usan el
   backend y los tests. La conversión vive solo en el frontend.
4. **Validación al escribir:** una fecha incompleta o inexistente (31/02/2026) muestra
   "Fecha inválida. Usá dd/mm/aaaa." y no se envía.
5. **Lectura:** todas las fechas que se muestran en pantallas y tablas pasan a dd/mm/aaaa. Los
   períodos de los PDF pasan a mm/aaaa ("Período: 01/2026 a 12/2026").
6. **Quedan como están:** los nombres de archivo de CSV y PDF (`ingresos-2026-01-2026-12.pdf`), que
   conviene que ordenen bien; el momento de la auditoría, que ya sale como dd/mm/aaaa (`es-AR`); y
   los 6 selectores de mes (`type="month"`) de los reportes, que no tienen día y no se confunden.

## Cambios

- `frontend/package.json` y `package-lock.json`: agrega `react-day-picker`.
- `frontend/src/shared/fechas.ts` (nuevo, puro): `formatearFecha("2026-11-01") → "01/11/2026"`,
  `formatearPeriodo("2026-11") → "11/2026"` y `parsearFecha("01/11/2026") → "2026-11-01" | null`.
- `frontend/src/shared/CampoFecha.tsx` (nuevo): el campo con el calendario. Mantiene el `<label>`
  asociado al campo, así los tests que buscan por etiqueta siguen andando.
- Carga, reemplaza los 6 `type="date"`: `ReservaForm` (inicio y fin), `CampaniaForm` (inicio y
  fin) y `Auditoria` (filtro desde y hasta).
- Lectura, pasa a `formatearFecha`: `ReservasCampania` (período), `CampaniaDetalle` (período),
  `CalendarioDisponibilidad` (detalle de la celda), `PanelPrincipal` (vencimiento) y `CostosPage`
  (fecha del costo).
- PDF: el texto "Período" de `ReporteIngresos`, `PorRubro` y `ReporteOcupacion` pasa a
  `formatearPeriodo`.

## Migraciones

Ninguna. No toca el backend.

## Reglas provisorias que se usan

Ninguna. Queda afuera RN-012 (no permitir fechas pasadas a mano), que también salió en la prueba
pero es una regla del backend y va en su propia unidad.

## Cómo se prueba

- `fechas.test.ts`: formateo, período, parseo válido, días inexistentes (31/02, 29/02 de un año no
  bisiesto), texto incompleto y vacío.
- `CampoFecha.test.tsx`: escribir dd/mm/aaaa devuelve `aaaa-mm-dd`; abrir el calendario y elegir un
  día; error con fecha inválida; Escape cierra.
- Se ajustan los tests existentes de `ReservaForm`, `CampaniaForm`, `Auditoria` y las pantallas de
  lectura que esperan fechas `aaaa-mm-dd` en el texto.
- A mano: repetir en `localhost` los pasos 5 a 8 de la prueba de reservas con Chrome en inglés.

## Registro de gates

- Gate 1 (plan): 2026-10-25 — aprobado por Juan Diego (react-day-picker; carga y lectura)
- Gate 2 (verificación): 2026-10-25 — frontend: `format:check` ok, `lint` sin hallazgos,
  `typecheck` ok, `test:coverage` 187 tests en verde (sentencias 87,91 %, líneas 90,97 %), `build`
  ok (bundle 827 kB; el aviso de más de 500 kB ya estaba en `develop` con 751 kB). Backend sin
  cambios: `ruff format --check` y `ruff check` ok, `mypy` sin errores, `makemigrations --check`
  sin cambios, `pytest --cov` 388 en verde (95,53 %). `pre-commit run --all-files` en verde,
  gitleaks incluido. Falta la prueba a mano en `localhost`.

## Pendiente fuera de esta unidad

- El mensaje de conflicto de cupo lo arma el backend con fechas `aaaa-mm-dd` ("entre 2026-11-01 y
  2026-11-30"). Pasarlo a dd/mm/aaaa es un cambio de `reservas` y va en otra unidad.
- Gate 3 (PR): pendiente
