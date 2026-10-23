# Unidad: Baja lógica en todo el sistema

- **Estado:** en revisión · **Épica:** E1 Seguridad y acceso · **App dueña:** `reservas`
  (+ `inventario`, `clientes`, `campanias`, `costos`, `auditoria`, `frontend`)
- **Origen:** HU-006 · **Rama:** `feature/reservas-baja-logica`

## Objetivo

Que ningún registro de negocio se borre físicamente en la operación diaria (HU-006). Los inactivos
no se ofrecen al cargar algo nuevo, pero siguen visibles donde ya estaban y en los reportes
históricos. La única excepción es que un administrador corrija una carga errónea sin actividad, y
eso queda auditado.

## Punto de partida (relevamiento del 23/10/2026)

**Criterio 1 (no hay eliminar en la interfaz ni en la API): cubierto.**

- Todos los `ViewSet` tienen `http_method_names` sin `delete` (`inventario`, `clientes`,
  `campanias`, `reservas`, `costos`, `usuarios`), y `auditoria` es `ReadOnlyModelViewSet`.
- El frontend no tiene ningún botón ni llamada `DELETE`.
- En el admin de Django solo están registrados `Rubro`, `Cliente` y `Marca` (con `SinBorrarAdmin`,
  que niega el borrado) e `IntentoIngreso`. Inventario, campañas, reservas y costos no están en el
  admin.
- No hay un test que lo fije. Se agrega uno que recorre las rutas y espera `405` en `DELETE`.

**Criterio 2 (un inactivo no se ofrece al crear): hay cuatro huecos.**

| Dónde | Hoy | Hueco |
| --- | --- | --- |
| `Marca` (cliente, rubro) | El servidor rechaza un inactivo nuevo y el formulario lo oculta | — |
| `Cartel` (formato, zona, proveedor, estado) | Igual | — |
| `Campania` (marca, cliente que factura) | El formulario oculta los inactivos con `vigentes()` | **El servidor acepta una marca o un cliente inactivo** |
| `Costo` (proveedor) | El formulario no elige proveedor | **El servidor acepta un proveedor inactivo** |
| `Reserva` (cartel) | El servidor rechaza un cartel de baja y la lista de carteles los oculta salvo con `incluir_bajas=1` | **Al editar una reserva de un cartel que se dio de baja, el selector no lo encuentra** (corregido el 23/10/2026: el relevamiento decía que el formulario ofrecía los carteles de baja, y no es así) |
| `Reserva` (cartel), al editar | El servidor rechaza el cartel de baja aunque no cambie | **No se puede editar una reserva vieja de un cartel que después se dio de baja**: `ReservaForm` siempre manda `cartel` |

**Criterio 3 (un inactivo sigue en los reportes históricos): hay un hueco.**

- `reporte_ingresos` y `reporte_por_rubro` (`facturacion`) no filtran por `activo`: incluyen
  clientes, marcas y rubros inactivos. Falta un test que lo fije.
- **`reporte_ocupacion` (HU-048) excluye los carteles de baja** (`estado__es_baja=False`), así que
  un cartel dado de baja con reservas en el período desaparece del histórico.
- `disponibilidad` de hoy y `calendario` también excluyen los carteles de baja. Eso está bien:
  muestran lo que se puede vender, no historia.

**Criterio 4 (el admin elimina una carga errónea sin actividad, y queda auditado): no existe.**

- Todas las FK de negocio son `on_delete=PROTECT`, así que la base ya impide borrar algo con
  actividad (un cartel con reservas, una marca con campañas, etc.).
- `CLAUDE.md` §5 dice "baja lógica (nunca `DELETE` desde la API)". Si el borrado fuera por la API,
  primero habría que cambiar esa regla con un PR `docs/` y un ADR.

## Preguntas al equipo

Respondidas por Gonza el 23/10/2026: se aceptan las opciones recomendadas o propuestas.


1. **App dueña y rama.** Toca `campanias`, `costos`, `reservas`, `auditoria` y `frontend`.
   - a) `feature/reservas-baja-logica`: reservas tiene el riesgo dominante y el hueco del cartel de
     baja. **(recomendado)**
   - b) `feature/inventario-baja-logica`.
   - c) Partirla en dos unidades: `baja-logica` (criterios 1 a 3) y `borrado-admin` (criterio 4).
2. **Por dónde borra el administrador (criterio 4).**
   - a) **Admin de Django**, como se decidió en `gestion-de-usuarios` (punto 4). Se registran los
     modelos que falten, se permite borrar solo al superusuario y solo si no hay actividad, y
     `delete_model` audita. No se toca la regla de `CLAUDE.md`. **(recomendado)**
   - b) **La API**, con `DELETE` solo para `SoloAdministrador` y un botón en la pantalla. Exige
     cambiar antes `CLAUDE.md` §5 por PR `docs/` con ADR.
   - c) Dejar el criterio 4 para más adelante.
3. **Qué se puede borrar (si 2 es a o b).** Propuesta: proveedores, formatos, zonas, estados,
   carteles, rubros, clientes, marcas y campañas, siempre que nada los referencie. Las **reservas y
   los costos no se borran**: se cancelan o se anulan (HU-006 y HU-044). ¿Está bien, o una reserva
   cargada por error también se puede borrar si no tiene costos?
4. **Cómo se audita el borrado.** Propuesta: igual que el alta en `gestion-de-usuarios`, una fila
   por campo con el valor anterior y el nuevo vacío, más una fila `campo="eliminado"`, de `""` a
   `"si"`, para filtrarlo fácil. ¿O alcanza con la fila `eliminado`?
5. **Reporte de ocupación (criterio 3).** Propuesta: incluir los carteles de baja **solo si tienen
   reservas que tocan el período**, marcados como "(de baja)". ¿O se incluyen siempre que el período
   sea anterior a la baja? (Esa fecha no se guarda hoy; habría que sacarla de auditoría.)

## Respuestas

1. `feature/reservas-baja-logica`.
2. Admin de Django; no se toca `CLAUDE.md` §5.
3. Se borran proveedores, formatos, zonas, estados, carteles, rubros, clientes, marcas y campañas
   sin nada que los referencie. Reservas y costos no se borran.
4. Una fila por campo (anterior → vacío) más la fila `eliminado` (`""` → `"si"`).
5. El reporte de ocupación incluye los carteles de baja con reservas en el período, marcados
   "(de baja)".

## Decisiones de diseño (mi criterio — corregir acá si hace falta)

6. **Mismo patrón que `Marca` y `Cartel`:** el servidor rechaza un inactivo solo si cambia. Si la
   campaña ya tenía esa marca, se puede seguir editando la campaña. Lo mismo para el cartel de baja
   en una reserva existente: se corrige el hueco de edición.
7. **El cartel expone `es_baja`** (solo lectura, desde su estado). `ReservasCampania` pide los
   carteles con `incluir_bajas=1` y `ReservaForm` oculta los de baja salvo el ya asignado. No se agrega un campo `activo` al cartel: la baja ya la da su estado.
8. **Fuera de alcance:** cargar reservas en una campaña cancelada. No es baja lógica; si hace falta,
   va en otra unidad.
9. **Roadmap:** en el mismo PR, HU-005 pasa a Hecho (quedó atrás según el handoff).
10. **Base compartida en `config/admin_borrado.py`** (como `config/permisos.py`):
    `BorradoAuditadoAdmin` deja borrar solo al superusuario y audita en la misma transacción, también
    en el borrado masivo. Si el registro tiene algo asociado, el `PROTECT` hace que el admin muestre
    qué lo referencia y no borra nada.
11. **Los admins nuevos (inventario y campañas) son de ver y borrar** (`SoloBorrarAdmin`): el alta y
    la edición siguen yendo por la aplicación, que valida y audita (por ejemplo, la tarifa del cartel).
    Clientes, marcas y rubros conservan el alta y la edición que ya tenían en el admin.
12. **Entidades en auditoría:** `proveedor`, `formato`, `zona`, `estado_cartel`, `cartel`, `rubro`,
    `cliente`, `marca` y `campania`. Se suman al filtro y a las etiquetas de la pantalla de Auditoría.
13. **Límite del reporte de ocupación:** un cartel que se dio de baja a mitad del período cuenta como
    disponible todo el período, porque la fecha de baja no se guarda.

## Cambios

- `backend/apps/campanias/serializers.py`: rechazar marca o cliente que factura inactivos si cambian.
- `backend/apps/costos/serializers.py`: rechazar un proveedor inactivo si cambia.
- `backend/apps/reservas/serializers.py`: rechazar el cartel de baja solo si cambia.
- `backend/apps/reservas/services.py`: `reporte_ocupacion` incluye los carteles de baja con reservas
  en el período (pregunta 5).
- `backend/apps/inventario/serializers.py`: `es_baja` de solo lectura en `CartelSerializer`.
- `backend/apps/auditoria/services.py`: `registrar_borrado`.
- `backend/config/admin_borrado.py` (nuevo): `BorradoAuditadoAdmin` y `SoloBorrarAdmin`.
- `backend/apps/inventario/admin.py` y `backend/apps/campanias/admin.py` (nuevos);
  `backend/apps/clientes/admin.py` cambia `SinBorrarAdmin` por `BorradoAuditadoAdmin`.
- `frontend/src/features/reservas/ReservasCampania.tsx` y `ReservaForm.tsx`: pedir los carteles con
  `incluir_bajas=1` y ocultar los de baja salvo el asignado, marcado "(de baja)".
- `frontend/src/features/reservas/ReporteOcupacion.tsx` y `ocupacion.ts`: marca "(de baja)" en la
  tabla, el CSV y el PDF.
- `frontend/src/features/auditoria/Auditoria.tsx`: las entidades nuevas en el filtro y las etiquetas.
- `docs/aidlc/roadmap.md`: HU-005 a Hecho. `docs/aidlc/reglas-de-negocio.md` no se toca: HU-006 no
  tiene RN propia.

## Migraciones

Ninguna.

## Reglas provisorias que se usan

Ninguna. HU-006 no tiene una RN asociada.

## Cómo se prueba

- `test_api_delete_cualquier_entidad_devuelve_405` (criterio 1, parametrizado por ruta).
- `test_campania_marca_inactiva_nueva_rechaza` y `..._sin_cambio_acepta`; lo mismo para el cliente
  que factura.
- `test_costo_proveedor_inactivo_nuevo_rechaza` y `..._sin_cambio_acepta`.
- `test_reserva_cartel_de_baja_sin_cambio_permite_editar`.
- `test_reporte_ocupacion_cartel_de_baja_con_reservas_lo_incluye` y `..._sin_reservas_lo_excluye`.
- `test_reporte_ingresos_cliente_inactivo_lo_incluye` y lo mismo para `reporte_por_rubro`.
- Criterio 4: `test_admin_borra_sin_actividad_audita`, `test_admin_borra_con_actividad_rechaza` y
  `test_admin_no_superusuario_no_borra`.
- Frontend: `ReservaForm` no ofrece un cartel de baja nuevo y sí muestra el asignado;
  `ReporteOcupacion` marca "(de baja)".

## Registro de gates

- Gate 1 (plan): 23/10/2026 — aprobado por Gonza
- Gate 2 (verificación): 23/10/2026 — aprobado por Gonza
  - `ruff format --check`: 113 files already formatted · `ruff check`: All checks passed!
  - `mypy backend`: Success: no issues found in 113 source files
  - `makemigrations --check --dry-run`: No changes detected
  - `pytest --cov`: 427 passed, coverage total 95.84 % (umbral 80 %), ningún test salteado
  - Frontend: `format:check` ok, `lint` (oxlint) sin hallazgos, `typecheck` ok,
    `test:coverage` 164 passed en 28 archivos (líneas 90.4 %, sentencias 87.25 %), `build` ok
    (solo el aviso de tamaño de chunk que ya existía)
  - `pre-commit run --all-files`: todos Passed, incluido gitleaks (Detect hardcoded secrets)
- Gate 3 (PR): #66
