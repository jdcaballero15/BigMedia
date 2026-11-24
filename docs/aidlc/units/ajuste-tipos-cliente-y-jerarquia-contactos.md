# Unidad: Tipos de cliente y jerarquía de contactos

- **Estado:** en curso · **Épica:** E3 Clientes, marcas y CRM · **App dueña:** clientes
- **Origen:** pedido de Juan Diego (2026-11-18), ajuste de HU-016, HU-068 y RN-015 · **Rama:** `feature/clientes-centrales-planificadores`

## Objetivo

Mostrar los tipos «Cliente directo», «Central de medios» e «Intermediario (bolsero)». En una central de medios, distinguir planificadores de asistentes y mostrar qué asistentes trabajan con cada planificador.

## Enfoques considerados

- **Recomendado:** conservar los códigos de tipo existentes y cambiar sus etiquetas. Extender `Contacto` con rol y un vínculo opcional al planificador. Conserva clientes, interacciones y referencias existentes.
- Reemplazar los códigos de tipo y crear entidades separadas para planificadores y asistentes. Exige migrar relaciones y duplicar los datos y formularios de contacto.

## Cambios

- `clientes`: `directo` se muestra como «Cliente directo», `intermediario_formal` como «Central de medios» e `intermediario` como «Intermediario (bolsero)». Los valores de la API y de la base no cambian.
- `clientes`: los contactos de una central tienen rol «Planificador» o «Asistente». Un asistente activo se vincula a un planificador activo de la misma central; un planificador no se vincula a otro contacto. El único contacto principal, si existe, debe ser planificador.
- `clientes`: validar el vínculo al crear o editar, impedir ciclos y rechazar cambios de rol o inactivaciones que dejen asistentes activos sin planificador. La API devuelve rol y planificador del contacto.
- `frontend`: actualizar etiquetas y filtros de tipos; en la ficha de una central, agrupar los asistentes debajo de cada planificador y ofrecer la selección del planificador al cargar o editar un asistente. Las interacciones siguen pudiendo elegir cualquier contacto activo de la central.
- `admin` y `docs/modelo-de-datos.md`: mostrar los nuevos datos y describir la relación.

## Migraciones

- Alterar las etiquetas de `Cliente.tipo` y agregar rol y clave foránea opcional a `Contacto`.
- Los contactos existentes conservan su identificador y sus interacciones. **Decisión propuesta:** migrarlos como planificadores, sin asistentes asociados; así la migración no inventa relaciones de supervisión.

## Reglas provisorias que se usan

- RN-015 sigue pendiente en el catálogo. Este pedido aporta la distinción entre tipos y la jerarquía; el ajuste del valor de RN-015 y de HU-016/HU-068 corresponde al PR `docs/historias-*` separado que exige el workflow.

## Cómo se prueba

- Backend: etiquetas de los tres tipos; migración de datos existentes; alta y edición de planificadores y asistentes; rechazo de planificador ajeno, inactivo o asistente; cambios de rol e inactivación con asistentes activos; contacto principal e interacciones conservadas.
- Frontend: opciones de tipo, listado jerárquico, formulario de asistente y selección de contacto en interacciones.
- Gate 2: comandos de la definición de terminado en `CLAUDE.md` §7, con salida real.

## Registro de gates

- Gate 1 (plan): 2026-11-18 — Juan Diego confirmó reutilizar `Contacto` con rol y vínculo entre asistente y planificador en la conversación.
- Gate 2 (verificación): 2026-11-18 — `pytest --cov -q`: 916 passed, cobertura 97,26 %; `ruff format --check .`: 145 archivos formateados; `ruff check .`: sin errores; `mypy backend`: sin errores en 145 archivos; `makemigrations --check --dry-run`: sin cambios; frontend: 421 tests, cobertura 92,95 % en sentencias y 94,91 % en líneas, `format:check`, `lint`, `typecheck` y `build` aprobados; `pre_commit run --all-files`: todos los hooks aprobados. Pendiente conformidad de Juan Diego.
- Gate 3 (PR): solo si se pide.
