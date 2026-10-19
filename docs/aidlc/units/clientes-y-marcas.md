# Unidad: Clientes y marcas

- **Estado:** en curso · **Épica:** E3 Clientes, marcas y CRM · **App dueña:** clientes
- **Origen:** HU-016, HU-017, HU-018 (roadmap: E3 es la próxima épica) · **Rama:** `feature/clientes-clientes-y-marcas`

## Objetivo

Que el equipo pueda cargar, buscar, editar e inactivar clientes (quien paga) y marcas (quien se
anuncia), con el rubro como catálogo editable, y que al crear un cliente directo se cree sola su marca
homónima. Es la base que necesitan las campañas (E4) y las reservas (E5).

## Decisiones tomadas con Juan Diego (18/10/2026)

- **Alcance:** HU-016, HU-017 y HU-018. Quedan para unidades siguientes: aviso de marcas duplicadas
  (HU-019), interacciones (HU-020), contactos de intermediarios formales (HU-068) y las fichas con
  campañas (HU-021, HU-022), que dependen de E4.
- **CUIT:** opcional; si se carga, se valida el formato (11 dígitos, se aceptan guiones) y el dígito
  verificador, y no puede repetirse entre clientes. Se guarda sin guiones.
- **Rubro:** catálogo editable (como formatos o departamentos), sin valores iniciales.

## Cambios

- **`clientes` (app nueva):**
  - `Rubro`: catálogo con `nombre` (único sin distinguir mayúsculas) y `activo`.
  - `Cliente`: `nombre` (de fantasía, el que se muestra), `razon_social`, `cuit` (opcional, único si
    existe), `tipo` (`directo`, `intermediario`, `intermediario_formal`), `telefono`, `correo`, `activo`,
    fechas de alta y modificación. Búsqueda por nombre o razón social sin distinguir mayúsculas ni tildes.
  - `Marca`: `nombre`, `cliente` (obligatorio, `PROTECT`), `rubro` (opcional), `activo`, fechas.
  - Servicio `crear_cliente`: crea el cliente y, si es directo, su marca homónima en la misma
    transacción (HU-018). Editar un cliente directo no duplica la marca.
    Cambiar el `tipo` después del alta no crea ni borra marcas: pasar a directo no crea la
    homónima y dejar de ser directo conserva la que ya tenía.
  - API en `/api/clientes/` (`clientes`, `marcas`, `rubros`) con los mismos permisos que el inventario:
    cualquier usuario con sesión lee y el grupo Operativo (o un superusuario) edita. Sin `DELETE`: se
    inactiva (baja lógica). Las listas ocultan los inactivos salvo que se pidan. Al crear o editar una
    marca no se ofrece un cliente inactivo.
  - Admin de Django para los tres modelos.
- **`config`:** el permiso "lee cualquiera con sesión, edita Operativo" pasa de
  `apps/inventario/views.py` a un módulo compartido (`config/permisos.py`), porque `clientes` no puede
  importar de `inventario` (`docs/arquitectura.md`). El inventario lo importa de ahí, sin cambio de
  comportamiento.
- **Frontend (`features/clientes`):** pantalla **Clientes** (lista con búsqueda, alta y edición,
  inactivar) y pantalla **Marcas** (lista filtrable por cliente y rubro, alta y edición, inactivar, y
  administración de rubros). La ficha de un cliente lista sus marcas. Dos pestañas nuevas en el menú.

## Migraciones

`clientes/0001_initial`: tablas `clientes_rubro`, `clientes_cliente` y `clientes_marca`. No mueve
datos ni toca tablas existentes. En Render se aplica sola al arrancar.

## Reglas provisorias que se usan

Ninguna. RN-016 (grupo económico) y RN-017 (cambio de razón social) siguen pendientes y no se
implementan: la marca homónima se crea una sola vez y después no se sincroniza con el cliente.

## Cómo se prueba

- Backend (pytest contra PostgreSQL, nombres `test_<qué>_<condición>_<resultado>`):
  - Cliente: alta con nombre, razón social y tipo; CUIT inválido rechazado; CUIT repetido rechazado;
    CUIT con guiones se normaliza; búsqueda por parte del nombre o la razón social, con y sin tildes.
  - Marca: sin cliente se rechaza por la API; un cliente inactivo no se acepta para una marca nueva;
    la lista de marcas de un cliente intermediario muestra todas las suyas.
  - HU-018: cliente directo crea su marca; intermediario e intermediario formal no; editar no duplica;
    si falla la creación de la marca, el cliente tampoco se crea.
  - Permisos: sin sesión 403; usuario sin grupo Operativo puede leer y no editar; no hay `DELETE`.
  - El inventario sigue pasando sus tests con el permiso movido.
- Frontend (Vitest): formulario de cliente (validación y envío) y lista con búsqueda; la cobertura
  del frontend se mantiene ≥ 80 %.
- Prueba manual en local: cargar un cliente directo y ver su marca creada.

## Registro de gates

- Gate 1 (plan): 2026-10-18 — aprobado por Juan Diego
- Gate 2 (verificación): pendiente
- Gate 3 (PR): pendiente
