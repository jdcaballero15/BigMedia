# Unidad: ajuste-campania-alta-con-posiciones

- **Estado:** en revisión · **Épica:** E10 Armado de campañas y reserva masiva · **App dueña:** campanias
  (con un ajuste chico en reservas)
- **Origen:** pedido de Juan Diego (2026-11-18) sobre HU-023, HU-055, HU-056 y HU-057 · **Rama:**
  `feature/frontend-campania-alta-con-posiciones`

## Objetivo

Que en el formulario de «Nueva campaña» se puedan agregar posiciones por formato y elegir carteles
antes de guardar. Nada se guarda hasta «Guardar campaña»: ahí se crean la campaña, sus líneas y sus
reservas, en ese orden.

## Decisiones (Juan Diego, 2026-11-18)

- **Todo junto al guardar**, no crear la campaña al abrir el formulario ni todo o nada. Si un cartel
  ya no tiene cupo al guardar, la campaña y el resto se guardan igual y se muestra cuáles fallaron y por
  qué (mismo criterio que la carga en bloque de HU-057).
- **Se descarta** el primer enfoque de esta unidad (abrir el detalle después de guardar): al guardar se
  vuelve a la lista, como antes.

## Requisito previo: PR de historias

El cambio amplía HU-055 y HU-056, que hoy dicen que las líneas y «Agregar carteles» se abren desde una
campaña existente («campaña precargada y bloqueada»). Antes del código va un PR
`docs/historias-carteles-en-alta-de-campania` con un criterio nuevo en HU-055 y HU-056 y su fila en
`registro-de-cambios.md`. No cambia ninguna regla RN.

## Cambios

- reservas (backend): `campania` pasa a ser opcional en `carteles-para-tanda` y `posiciones`
  (`_parametros_de_tanda`). Sin campaña, ningún cartel figura como «ya en la campaña». El resto de la
  validación (formato, fechas, filtros, cupo) no cambia. `en-bloque` no cambia: se llama con la
  campaña ya creada.
- frontend `features/reservas/AgregarCarteles.tsx`: un modo «solo elegir» que devuelve la selección al
  formulario en vez de crear reservas. El modo actual, desde el detalle, no cambia.
- frontend `features/campanias/CampaniaForm.tsx` (solo en el alta): sección «Posiciones por formato»
  con formato, cantidad opcional, «Agregar carteles» y el contador de carteles elegidos. Para elegir
  carteles hacen falta fechas: las de la campaña o las que se carguen en «Agregar carteles».
- frontend `features/campanias/CampaniasPage.tsx`: al guardar el alta, POST de la campaña, POST de
  cada línea y reservas en bloque por formato, con las mismas fechas que se usaron para elegir. Si algo
  falla después de crear la campaña, se muestra un resumen (líneas o carteles que no se pudieron crear,
  con su motivo) y la campaña queda creada.
- La edición de una campaña no cambia.

## Migraciones

Ninguna.

## Reglas provisorias que se usan

Ninguna nueva. La validación de cupo (RN-001, RN-002, RN-003) sigue corriendo en el servidor al crear
cada reserva; el listado previo es solo orientativo.

## Cómo se prueba

- Backend (`test_reservas_*`): `carteles-para-tanda` y `posiciones` sin `campania` devuelven los
  carteles con cupo y `en_campania` falso; con un `campania` inválido siguen dando 400 o 404.
- Frontend: el alta permite agregar una línea y elegir carteles sin guardar; al guardar se hacen el POST
  de la campaña, el de la línea y el de `en-bloque` con el `id` nuevo; si fallan carteles, se muestra el
  resumen; si se cancela, no se hace ningún POST; la edición no muestra la sección nueva.
- `AgregarCarteles`: el modo «solo elegir» no llama a `en-bloque`.
- Definition of Done completa (`CLAUDE.md` §7).

## Coordinación

- Worktree `../bigMedia-alta-campania`, aparte de `bigMedia/` y de las otras terminales.
- Ninguna rama abierta toca `CampaniasPage`, `CampaniaForm`, `AgregarCarteles` ni las vistas de
  `reservas` (revisado el 2026-11-18).

## Registro de gates

- Gate 1 (plan, primer enfoque): 2026-11-18 — aprobado por Juan Diego; descartado tras probarlo.
- Gate 1 (plan, enfoque actual): 2026-11-18 — aprobado por Juan Diego
- Gate 2 (verificación): 2026-11-18 — `ruff format --check` 144 archivos ya formateados (la
  primera corrida marcó los dos tests nuevos; se formatearon) y `ruff check` sin errores; `mypy
  backend` sin errores en 144 archivos; `makemigrations --check` sin cambios; `pytest --cov` 875
  passed, 0 salteados, coverage 97.42 %; pre-commit `--all-files` exit 0 (gitleaks incluido).
  Frontend: `format:check`, `lint` (exit 0), `typecheck` y `build` en verde; `test:coverage` 434
  passed en 51 archivos, líneas 95.04 %, sentencias 93.1 %. Tests de frontend escritos después del
  código. Aprobado por Juan Diego tras probarlo.
- Gate 3 (PR): #145 (código) y #144 (historias), abiertos el 2026-11-18 a pedido de Juan Diego
