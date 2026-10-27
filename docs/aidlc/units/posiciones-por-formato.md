# Unidad: Posiciones por formato

- **Estado:** en curso · **Épica:** E10 Armado de campañas y reserva masiva · **App dueña:** `campanias`
- **Origen:** HU-055, más los criterios 1 y 2 de HU-058 · **Rama:** `feature/campanias-posiciones-por-formato`

## Objetivo

Que la campaña lleve líneas de formato con la cantidad de posiciones que se necesitan (por ejemplo
"Gran Formato: 100"). En cada línea se ve cuántas posiciones se pidieron, cuántas ya están
reservadas y cuántas faltan. Esta es la primera de las tres unidades de E10, y la base de la
pantalla "Agregar carteles".

## Decisiones

1. **E10 en tres unidades** (Gonza, 27/10/2026): esta unidad; `reserva-masiva` (HU-056 y HU-057);
   y `confirmacion-en-bloque` (HU-059, más los criterios 3 y 4 de HU-058, que piden actualizar las
   reservas Pendientes cuando cambian las fechas de la campaña).
2. **La línea vive en `campanias`** (Gonza, 27/10/2026): así lo dice ya la tabla de apps. Como la
   línea apunta a `inventario.Formato`, el [ADR-0007](../../adr/0007-campanias-importa-de-inventario.md)
   habilita que `campanias` importe de `inventario`. `inventario` no importa de ninguna app, así
   que no se arma ningún ciclo.
3. **El seguimiento se calcula en `reservas`** (propuesta): para contar las reservadas hacen falta
   las reservas, y `campanias` no puede importar de `reservas`. Por eso el cálculo vive en
   `reservas/services.py` y se expone en `GET /api/reservas/seguimiento/?campania=<id>`.
4. **Quitar una línea es una baja lógica** (propuesta): la API no expone `DELETE` (CLAUDE.md §5).
   Una línea quitada queda con `activa=False` y deja de verse. El formato no se puede repetir
   entre las líneas activas de una misma campaña (criterio 3), así que, después de quitar una
   línea, se puede volver a agregar ese formato.
5. **Cómo se cuenta** (propuesta): una reserva es "reservada" para una línea cuando pertenece a la
   campaña, su cartel es de ese formato y no está Cancelada. Esto incluye Pendientes, Confirmadas
   y Finalizadas (HU-058). Faltantes = `max(0, solicitadas − reservadas)`. Si se reservó más de lo
   solicitado, se muestra el excedente aparte ("+5"). Si la línea no tiene cantidad, se muestran
   solo las reservadas (criterio 2).
6. **Reservas de formatos sin línea** (propuesta): el seguimiento las muestra en filas aparte, sin
   cantidad solicitada, para que lo reservado coincida con el total de la campaña. No se crea
   ninguna línea automáticamente.
7. **Formatos inactivos:** al agregar una línea solo se ofrecen formatos activos. Si un formato se
   inactiva después, la línea que ya lo usa se conserva.
8. **Fuera de alcance:** la pantalla "Agregar carteles", el monto estimado y la creación en bloque
   (unidad `reserva-masiva`). Tampoco entra la actualización de fechas de las Pendientes
   (unidad `confirmacion-en-bloque`).

## Cambios

- `campanias/models.py`: modelo `LineaFormato` con `campania` (FK, `PROTECT`, `related_name="lineas"`),
  `formato` (FK a `inventario.Formato`, `PROTECT`), `cantidad` (`PositiveIntegerField`, opcional,
  mínimo 1), `activa`, `creado_en` y `actualizado_en`. Tiene un `UniqueConstraint(campania, formato)`
  condicionado a `activa=True`.
- `campanias/serializers.py` y `views.py`: CRUD sin `DELETE` en `/api/campanias/lineas-formato/`,
  filtrable por `campania`, con los mismos permisos que las campañas. Quitar la línea es un
  `PATCH` con `activa=false`. El choque de formato repetido devuelve un mensaje claro y no un error
  de integridad (criterio 3).
- `reservas/services.py`: `seguimiento_de_campania(campania)` devuelve, por línea activa,
  formato, solicitadas, reservadas, faltantes y excedente, más las filas de formatos sin línea.
- `reservas/views.py` y `urls.py`: `SeguimientoView` en `/api/reservas/seguimiento/?campania=<id>`.
- Frontend `features/campanias/PosicionesPorFormato.tsx`: sección "Posiciones por formato" en el
  detalle de la campaña. Tiene una tabla de formato, solicitadas, reservadas y faltantes; un alta
  con selector de formato y cantidad opcional; la edición de la cantidad; y "Quitar". Solo se puede
  editar con permiso de edición.
- Docs: `CLAUDE.md` §2 y `docs/arquitectura.md` suman `inventario` a lo que puede importar
  `campanias`. En la tabla de apps de `docs/arquitectura.md`, `campanias` y `reservas` pasan a
  "implementada" y `clientes` deja de figurar como parcial (pendiente anotado en el handoff).
  Además, se agregan las filas de las tres unidades en `units.md` y E10 queda "En curso" en el roadmap.

## Migraciones

Una nueva en `campanias`: crea `LineaFormato` y su restricción única condicional. No mueve datos.

## Reglas provisorias que se usan

Ninguna regla nueva. El conteo de reservadas sigue a HU-058: las Canceladas no cuentan. No depende
de RN-002 (si la Pendiente bloquea o no): una Pendiente cuenta como reservada en el seguimiento.

## Cómo se prueba

- `backend/tests/test_lineas_formato.py`: alta con formato y cantidad (criterio 1); alta sin cantidad
  (criterio 2); formato repetido rechazado con mensaje (criterio 3); cantidad cambiada o línea
  quitada sin alterar reservas (criterio 4); volver a agregar un formato quitado; cantidad 0
  rechazada; sin `DELETE`; usuario de Lectura sin escritura.
- `backend/tests/test_seguimiento.py`: 100 solicitadas, 60 reservadas y 40 faltantes (HU-058,
  criterio 1); línea sin cantidad (criterio 2); Canceladas sin contar; excedente; formato sin
  línea; campaña inexistente o ID inválido.
- Frontend `PosicionesPorFormato.test.tsx`: tabla con los conteos, alta, error de formato repetido,
  edición, quitar y vista de solo lectura.

## Registro de gates

- Gate 1 (plan): 2026-10-27 — aprobado por Gonza
- Gate 2 (verificación): 2026-10-27 — `ruff format --check` (119 archivos) y `ruff check`
  sin errores; `mypy backend` sin errores (119 archivos); `makemigrations --check` sin cambios;
  `pytest --cov`: 565 tests en verde, coverage 96,26 %; frontend `format:check`, `lint`,
  `typecheck` y `build` en verde, `test:coverage` con 238 tests en verde y 92,22 % de líneas
  (89,41 % de sentencias); `pre-commit run --all-files` (gitleaks incluido) en verde.
  Espera revisión de Gonza o Juan Diego.
- Gate 3 (PR): pendiente
