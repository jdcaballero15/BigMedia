# Unidad: recordatorio-de-interaccion

- **Estado:** en revisión · **Épica:** E3 Clientes, marcas y CRM · **App dueña:** campanias
- **Origen:** HU-072 (pedido de Gonza, 2026-11-19) · **Rama:** `feature/campanias-recordatorio-de-interaccion`

## Objetivo

Que una interacción pueda llevar un recordatorio (fecha y qué hacer, por ejemplo «Enviar
presupuesto»), que ese día aparezca en el Panel para todo el equipo hasta que alguien lo marque
como hecho.

## Dependencias

La rama sale de `feature/frontend-interacciones-en-ficha-cliente`, porque se carga desde la ficha
del cliente con el formulario de esa unidad. HU-072 está en `docs/historias-recordatorio-de-interaccion`.
Orden de los PR: primero esos dos y después este, con la rama rebasada sobre `develop`.

## Cambios

- campanias, `models.py`: `Interaccion` suma `recordatorio_fecha` (fecha, opcional),
  `recordatorio_texto` (hasta 200 caracteres, opcional), `recordatorio_hecho_en` y
  `recordatorio_hecho_por` (no editables desde la API).
- campanias, `services.py`:
  - `validar_recordatorio(fecha, texto)`: van juntos o ninguno (HU-072 criterio 2).
  - `marcar_recordatorio_hecho(interaccion_id, usuario)`: en `transaction.atomic()` con
    `select_for_update()`, guarda cuándo y quién; rechaza una interacción sin recordatorio o
    con el recordatorio ya hecho.
- campanias, `serializers.py`: los dos campos editables, y `recordatorio_hecho_en` y
  `recordatorio_hecho_por_nombre` de solo lectura; `validate` llama a `validar_recordatorio`.
- campanias, `views.py`:
  - filtro `?recordatorio=pendiente`: con fecha de hoy o anterior (`timezone.localdate()`) y sin
    hacer, del más viejo al más nuevo;
  - acción `POST /api/campanias/interacciones/<id>/recordatorio-hecho/`, con el mismo permiso que
    editar (el rol Lectura recibe 403).
- frontend, `features/campanias/InteraccionForm.tsx`: campos «Fecha de recordatorio» y «Qué
  hacer», opcionales.
- frontend, `features/campanias/InteraccionesLista.tsx`: columna «Recordatorio» con la fecha, qué
  hacer y «Pendiente» o «Hecho». También se ve en el detalle de campaña y en la ficha de marca,
  que siguen de solo lectura.
- frontend, `features/panel/`: bloque «Recordatorios» en el Panel con fecha, qué hacer, cliente y
  quién cargó la interacción; los de días anteriores marcados «Vencido»; botón «Hecho» solo con
  permiso de edición; vacío: «No hay recordatorios para hoy.»
- docs, `docs/manual/manual-de-uso.md`: cómo cargar un recordatorio y marcarlo como hecho.

Queda fuera, como dice HU-072: correo y recordatorios sin interacción. Tampoco hay un link del
Panel a la ficha del cliente: hoy el Panel no navega a otras pantallas, y HU-072 no lo pide.

## Decisión (Gonza, 2026-11-19)

- **Editar un recordatorio hecho.** Si se cambia la fecha o el texto de un recordatorio ya hecho,
  vuelve a quedar pendiente; si se borran los dos, la interacción queda sin recordatorio.
  Así no hace falta un botón para reabrirlo.

## Migraciones

`campanias/0010_interaccion_recordatorio`: suma las cuatro columnas, todas opcionales. No mueve
datos.

## Reglas provisorias que se usan

Ninguna. HU-072 no trae una regla RN nueva.

## Cómo se prueba

- Backend, `backend/tests/test_interacciones.py`, contra PostgreSQL:
  - `test_recordatorio_con_fecha_y_texto_se_guarda`;
  - `test_recordatorio_sin_texto_o_sin_fecha_se_rechaza`;
  - `test_pendientes_incluye_hoy_y_vencidos_ordenados_y_excluye_futuros_y_hechos`;
  - `test_marcar_hecho_guarda_usuario_y_momento`;
  - `test_marcar_hecho_sin_recordatorio_o_ya_hecho_se_rechaza`;
  - `test_marcar_hecho_con_rol_lectura_devuelve_403`;
  - `test_editar_recordatorio_hecho_lo_vuelve_pendiente`.
- Frontend:
  - `InteraccionForm.test.tsx`: envía fecha y qué hacer;
  - `InteraccionesLista.test.tsx`: la columna muestra pendiente y hecho;
  - `PanelPrincipal.test.tsx`: lista los pendientes, marca vencidos, «Hecho» manda el `POST` y
    lo saca de la lista, Lectura no ve el botón, vacío y error.
- Verificación completa de la Definition of Done (`CLAUDE.md` §7).

## Registro de gates

- Gate 1 (plan): 2026-11-19 — aprobado por Gonza, con la opción recomendada para editar un
  recordatorio hecho
- Gate 2 (verificación): 2026-11-20 — `ruff format --check` (145 archivos ya formateados) y
  `ruff check` (All checks passed!); `mypy backend` (no issues found in 145 source files);
  `makemigrations --check --dry-run` (No changes detected); `pytest --cov` (926 passed, 97.52 %,
  ninguno salteado); `pre-commit run --all-files` con gitleaks (salida 0, 13 hooks Passed);
  frontend `format:check`, `lint`, `typecheck` sin errores, `test:coverage` (441 passed en 50
  archivos; sentencias 92.75 %, ramas 83.84 %, líneas 94.67 %) y `build` (built in 275ms). El
  19/11 `test:coverage` falló tres veces por tiempo con la máquina saturada (carga 250); con la
  carga normal pasó entero. Aprobado por Gonza (2026-11-20).
- Gate 3 (PR): #152 (historias en #151)
