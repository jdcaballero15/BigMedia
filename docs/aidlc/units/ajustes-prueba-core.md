# Unidad: ajustes-prueba-core

- **Estado:** en curso · **Épica:** — (ajustes de prueba manual) · **App dueña:** `frontend`, `campanias`
- **Origen:** prueba manual de Juan Diego (2026-11-16), HU-020, HU-042, HU-044 y HU-045 · **Rama:** `feature/frontend-ajustes-prueba-core`

## Objetivo

Hacer legibles los importes de costos y rentabilidad, mostrar junto al calendario el detalle de la celda seleccionada y permitir registrar una interacción sin asunto.

## Cambios

- `frontend/features/costos`: presentar ingresos, costos y márgenes con `$`, separadores argentinos y dos decimales en la reserva, la campaña y la lista de costos. Los campos de carga siguen siendo numéricos.
- `frontend/features/disponibilidad`: al elegir una celda ocupada, mostrar su detalle junto a la fila del cartel. Incorporar selección de período de hasta 12 meses, ya prevista en HU-042.
- `campanias` y `frontend/features/campanias`: admitir asunto vacío en Interacciones y mostrar «Sin asunto» al consultarlas. La fecha y el cliente siguen obligatorios.
- Antes del cambio de HU-020, ajustar su texto y criterio 1 en un PR separado `docs/historias-asunto-opcional`, con entrada en `inputs/registro-de-cambios.md`. Ese PR no lleva código.

## Fuera de alcance

- Cambiar los estados de campañas o reservas.
- Crear la vista visual de posiciones basada en `posiciones 8-10.xlsx`; tendrá su propia unidad.
- Cambiar cálculos de importes, costos, márgenes o disponibilidad.

## Migraciones

Una migración de `campanias.Interaccion.asunto` para admitir vacío (`blank=True`); sin transformación ni pérdida de datos.

## Reglas provisorias que se usan

Ninguna nueva. HU-020 debe actualizarse en el PR de historias previo. HU-042 ya prevé hasta 12 meses.

## Cómo se prueba

- Los importes positivos, cero y negativos se muestran en pesos en los tres lugares; los valores calculados no cambian.
- Al tocar una celda ocupada, el detalle aparece junto a su cartel; al elegir otra, se actualiza; una celda libre no abre detalle.
- El rango del calendario admite hasta 12 meses y muestra reservas del período elegido.
- Una interacción sin asunto se guarda y se muestra como «Sin asunto» en lista y fichas; una con asunto conserva su texto.
- Verificación completa de backend y frontend, migraciones y pre-commit, con salida real en Gate 2.

## Registro de gates

- Gate 1 (plan): 2026-11-16 — aprobado por Juan Diego en esta conversación
- Gate 2 (verificación): 2026-11-16 — `ruff format --check`: 144 archivos formateados; `ruff check`: All checks passed; `mypy backend`: Success, no issues found in 144 source files; `makemigrations --check --dry-run`: No changes detected; `pytest --cov`: 890 passed, 0 skipped, cobertura total 97,30 % (mínimo 80 %); `pre-commit run --all-files`: 13 hooks Passed, incluido gitleaks de los cambios preparados; frontend `format:check`, `lint`, `typecheck` y `build`: exit 0; `test:coverage`: 397 passed, 50 archivos, sentencias 92,72 %, ramas 84,06 %, líneas 94,8 %. `gitleaks detect --source . --no-git --redact` local (v8.30.1): exit 1, tres hallazgos preexistentes ajenos al diff (dos en `backend/.env` ignorado y uno en `backend/tests/test_asegurar_admin.py:10`); CI fija v8.21.2. Build: warning de chunk >500 kB.
- Gate 3 (PR): pendiente
