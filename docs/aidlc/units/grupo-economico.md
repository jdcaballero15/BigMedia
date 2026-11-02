# Unidad: grupo-economico

- **Estado:** mergeada (PR #92) · **Épica:** E3 Clientes, marcas y CRM (y el resto de E8) · **App dueña:** clientes
- **Origen:** RN-016, HU-017 (grupo), HU-022 criterio 2, HU-050 criterio 2 · **Rama:** `feature/clientes-grupo-economico`

## Objetivo

Que las marcas se puedan agrupar en grupos económicos, que la ficha de una marca muestre las otras
marcas de su grupo, y que gerencia corte ingresos y ocupación por grupo, igual que ya lo hace por
rubro.

## Encuadre

- **RN-016 (`provisoria`, 2026-10-28):** catálogo editable de grupos, como los rubros. Cada marca
  pertenece a lo sumo a un grupo; es opcional e independiente del cliente que factura. Editan
  Operativo y Administrador.
- **App dueña:** `clientes` (modelo, API y pantalla del catálogo). El reporte vive en `facturacion`,
  que ya puede importar de `clientes`. Sin dependencias nuevas entre apps.
- **Capas:** backend (`clientes` y `facturacion`) y frontend (`features/clientes` y
  `features/facturacion`).

## Cambios

### Backend

- `clientes/models.py`: modelo `GrupoEconomico` (`nombre`, `activo`), con la misma restricción de
  nombre único sin distinguir mayúsculas que `Rubro`. `Marca.grupo`: `ForeignKey` a
  `GrupoEconomico`, opcional, `on_delete=PROTECT`, `related_name="marcas"`.
- `clientes/serializers.py`: `GrupoEconomicoSerializer` (como `RubroSerializer`, con su mensaje de
  nombre repetido). `MarcaSerializer` suma `grupo` y `grupo_nombre`; solo acepta un grupo activo,
  igual que el rubro.
- `clientes/views.py` y `urls.py`: `GrupoEconomicoViewSet` en `/api/clientes/grupos/`, con los
  mismos permisos que los rubros (`LecturaConSesionEdicionOperativo`) y baja lógica (`activo`).
  `MarcaViewSet` acepta el filtro `?grupo=<id>`.
- `facturacion/services.py`: `reporte_por_grupo(desde, hasta)`, con las mismas cuentas que
  `reporte_por_rubro` (ingresos repartidos por mes y días-cupo). Las marcas sin grupo caen en
  «Sin grupo». Las dos funciones comparten un acumulador común para no duplicar las cuentas;
  `reporte_por_rubro` devuelve exactamente lo mismo que hoy.
- `facturacion/views.py` y `urls.py`: `PorGrupoView` en `GET /api/facturacion/por-grupo/`, solo para
  Gerencia y con los mismos parámetros y errores que `por-rubro`.
- Migración `clientes.00xx_grupo_economico`, revisada a mano: crea la tabla y la columna nullable,
  sin datos.

### Frontend

- `features/clientes/CatalogoAdmin.tsx` (nuevo): el ABM de un catálogo de nombres (crear, renombrar,
  inactivar), parametrizado por ruta y etiquetas. `RubrosAdmin` pasa a usarlo sin cambiar lo que
  muestra; `GruposAdmin` es el otro uso. Va debajo de los rubros en **Comercial › Marcas**.
- `MarcaForm.tsx`: selector opcional «Grupo económico» con los grupos activos. El alta rápida de
  marca desde una campaña no lo ofrece (el grupo se asigna después desde Marcas), para no cargar el
  catálogo en Campañas.
- `MarcasPage.tsx`: columna «Grupo» en la tabla y filtro por grupo. La ficha de la marca suma
  «Otras marcas del grupo <nombre>» (solo si tiene grupo), con nombre, cliente y estado de cada una.
- `features/facturacion/PorRubro.tsx`: un selector «Cortar por: Rubro / Grupo económico» que cambia
  el endpoint y la primera columna. La pantalla y el ítem del menú pasan a llamarse «Por rubro o
  grupo». CSV y PDF exportan el corte elegido.
- Manual de uso: cómo cargar grupos y asignarlos, y el corte por grupo.

## Fuera de alcance

- Grupos de clientes (agencias): la regla agrupa marcas.
- Que una marca esté en más de un grupo.
- Importar grupos desde una planilla.
- Cambiar el grupo de marcas en tanda.

## Migraciones

Una, aditiva: tabla `clientes_grupoeconomico` y columna `clientes_marca.grupo_id` nullable. No toca
datos existentes; las marcas quedan sin grupo.

## Reglas provisorias que se usan

- RN-016 (grupo económico), que se aplica en esta unidad: su columna «Dónde vive» se completa en este
  PR.
- RN-004 (una reserva = un cupo), para los días-cupo del reporte, como en el corte por rubro.

## Cómo se prueba

- Backend (PostgreSQL real, `@pytest.mark.regla("RN-016")` donde corresponde):
  - `test_grupos_economicos.py`: crear, renombrar e inactivar grupos; nombre repetido sin distinguir
    mayúsculas → 400; Lectura no puede escribir; no hay `DELETE`.
  - Marca: asignar y quitar el grupo; un grupo inactivo o inexistente → 400; filtro `?grupo=`.
    Dos marcas de clientes distintos en el mismo grupo se aceptan (independiente del cliente).
  - `test_reporte_por_grupo.py`: suma ingresos y días-cupo de las marcas del grupo (HU-050
    criterio 2); marcas sin grupo → «Sin grupo»; respeta el período; solo Gerencia; formato de
    período inválido → 400. `test_reporte_por_rubro.py` sigue pasando sin cambios.
- Frontend:
  - `CatalogoAdmin` (por `RubrosAdmin` y `GruposAdmin`): crear, renombrar, inactivar; Lectura no ve
    los botones de edición.
  - `MarcaForm`: envía el grupo elegido o `null`.
  - `MarcasPage`: la ficha de una marca con grupo lista las otras marcas del grupo (HU-022 criterio
    2); sin grupo, la sección no aparece.
  - `PorRubro`: al cambiar a «Grupo económico» pide `por-grupo` y muestra la columna «Grupo».
- Definition of Done completa.

## Preguntas

Ninguna abierta: RN-016 se respondió el 2026-10-28 (ver `reglas-de-negocio.md`).

## Registro de gates

- Gate 1 (plan): 2026-10-28 — aprobado por Gonza
- Gate 2 (verificación): 2026-10-28 — `ruff format --check`: 137 files already formatted;
  `ruff check`: All checks passed!; `mypy backend`: Success: no issues found in 137 source files;
  `makemigrations --check --dry-run`: No changes detected; `pytest --cov`: 787 passed, coverage
  96.90 % (requerido 80 %); `pre-commit run --all-files`: todos Passed (incluido gitleaks).
  Frontend: `format:check` OK, `lint` sin hallazgos, `typecheck` OK, `test:coverage` 344 passed
  (sentencias 91.6 %, ramas 81.83 %, líneas 93.92 %), `build` OK (aviso de bloque mayor a 500 kB,
  previo a esta unidad).
  Después del rebase sobre `develop` con `estilo-base` (2026-10-28): `CatalogoAdmin` pasa
  «Inactivar» al menú de tres puntos (`MenuFila`), como el resto de las tablas. Verificación
  repetida: ruff y mypy sin errores (137 archivos), `makemigrations --check` sin cambios, pytest
  787 passed (96,90 %), frontend 353 tests (sentencias 91,79 %, líneas 94,06 %), lint,
  typecheck y build en verde, pre-commit todo Passed.
- Gate 3 (PR): pedido por Gonza el 2026-10-28; PR #92.
