# Unidad: Campañas

- **Estado:** mergeada · **Épica:** E4 Campañas · **App dueña:** `campanias`
- **Origen:** HU-023, HU-024 (usa RN-011 y RN-014) · **Rama:** `feature/campanias-crear-y-estados`

## Objetivo

Permitir al rol Operativo crear y editar campañas (contenedor comercial de un cliente/marca) con sus
cuatro estados, dejando la campaña lista para colgarle reservas y costos en E5/E7. Refleja el flujo que
pidió Seba: cargar cliente + campaña primero y, más adelante, agregar reservas desde la campaña.

## Cambios

- `campanias` (app nueva): modelo `Campania`, serializer, viewset (sin DELETE), rutas bajo
  `/api/campanias/`, `services.py` para la regla de confirmación, migración inicial + permisos al
  grupo Operativo. Importa de `clientes` (permitido por arquitectura); **no** importa `inventario` ni
  `reservas`.
- `config`: registrar `apps.campanias` en `INSTALLED_APPS` y montar sus urls.
- `frontend/src/features/campanias/`: `CampaniasPage` (tabla + filtro por estado + búsqueda),
  `CampaniaDetalle` (hub con datos, selector de estado y secciones "Reservas" y "Costos" marcadas
  *próximamente*), `CampaniaForm` (alta/edición; crear marca al vuelo reusando el `MarcaForm` de
  `clientes`), `types.ts`. Entrada de navegación "Campañas" en `App.tsx`.

### Modelo `Campania`

| Campo | Tipo | Regla |
| --- | --- | --- |
| `nombre` | CharField(blank) | Opcional (HU-023: ningún campo obligatorio para guardar). |
| `marca` | FK `clientes.Marca` (PROTECT, null) | Opcional. El anunciante. |
| `cliente_facturacion` | FK `clientes.Cliente` (PROTECT, null) | Opcional. Si se carga, reemplaza la deducción desde la marca (RN-014). |
| `fecha_inicio` / `fecha_fin` | DateField(null) | Opcionales. Intención comercial; no se derivan de reservas. |
| `estado` | TextChoices | `cotizada` (default) · `confirmada` · `cancelada` · `perdida`. |
| `creado_en` / `actualizado_en` | DateTime | `auto_now_add` / `auto_now`. |

- **Cliente que factura (derivado, solo lectura):** `cliente_facturacion` si está; si no, `marca.cliente`
  cuando hay marca; si no, vacío (HU-023 criterio 2).
- La campaña **no** usa baja lógica (`activo`): su ciclo es el `estado`. Sin `DELETE`: canceladas y
  perdidas siguen visibles en el histórico (HU-024 criterio 3).

### API

- `/api/campanias/campanias/`: `GET` (lista), `POST`, `GET/PATCH {id}`. `DELETE` → 405.
- Permiso compartido `config.permisos.LecturaConSesionEdicionOperativo`.
- Filtros de lista: `estado`, `q` (búsqueda sin tildes sobre nombre), `marca`.
- Confirmar (pasar `estado` a `confirmada`) exige marca + cliente que factura (derivado) + ambas
  fechas (RN-011); la regla vive en `services.py`.

## Migraciones

Una migración inicial: tabla `campania` con sus FKs a `clientes`, y una migración de datos que otorga
`view/add/change` de `Campania` al grupo `Operativo` (patrón de `clientes`/`inventario`). No mueve datos.

## Reglas provisorias que se usan

- **RN-011** (provisoria, valor vigente: para confirmar se exigen cliente, marca y fechas). Este unit la
  aplica en la transición a `confirmada`; el PR de código solo actualiza su columna "Dónde vive".
- **RN-014** (hoy `pendiente`). **Decisión de Seba (2026-10-19):** una marca *sí* puede cambiar de
  agencia o comprarse por dos clientes, por eso la campaña lleva `cliente_facturacion` propio y HU-027
  queda viva. Cambiar el valor/estado de RN-014 en el catálogo va en un **PR docs aparte**
  (`docs/historias-campanias-rn014`), no en este PR de código.

## Diferido (no entra en este unit)

- **HU-023 criterio 4** (lista de reservas de la campaña con acceso para agregar) y el flujo
  campaña→reserva: la vista de detalle deja la sección "Reservas" como *próximamente*; se llena en E5.
- **HU-025** (monto total y cantidad de reservas): depende de HU-028 (reservas). Sección "Costos"
  también *próximamente* (E7).
- **HU-024 criterio 2** (panel que cuenta campañas activas): es de reportes (E8); acá solo queda el
  filtro por estado que lo habilita.
- **HU-027 completo** (estampar el cliente anterior en campañas al cambiar la marca): el campo existe,
  pero esa mecánica de estampado se hará en su propio unit de ajuste.
- **Input de Seba para E5** (reservas con cantidad+tipo+importes sin posición exacta en circuitos
  grandes — séxtuples/PPL/banderolas/carteleras): se registra en un **PR docs aparte** sobre las
  preguntas abiertas de E5.

## Cómo se prueba

- Backend (`backend/tests/test_campanias.py`, PostgreSQL real):
  - crear campaña vacía → 201 (HU-023 criterio 1).
  - crear con marca → `cliente_factura` derivado = `marca.cliente` (HU-023 criterio 2).
  - `cliente_facturacion` propio reemplaza la deducción (RN-014).
  - confirmar sin marca/cliente/fechas → 400; con todo → 200 (`@pytest.mark.regla("RN-011")`).
  - canceladas y perdidas siguen en la lista (HU-024 criterio 3).
  - anónimo/sin permiso no escriben (401/403); `DELETE` → 405; escritura sin CSRF → 403.
- Frontend (Vitest): `CampaniasPage` lista y filtra por estado; `CampaniaForm` crea una campaña y
  permite crear una marca al vuelo; `CampaniaDetalle` muestra el cliente que factura y las secciones
  *próximamente*.

## Decisiones

- **RN-014 (Seba, 2026-10-19):** campaña con `cliente_facturacion` propio (ver arriba).
- **Pantalla (Juan Diego, 2026-10-19):** tabla + vista de detalle hub, con Reservas/Costos marcadas
  *próximamente*.
- **Alcance (Juan Diego, 2026-10-19):** HU-023 + HU-024; HU-025 diferida hasta reservas.

## Registro de gates

- Gate 1 (plan): 2026-10-19 — aprobado por Juan Diego.
- Gate 2 (verificación): 2026-10-19 — `ruff format --check` y `ruff check` sin errores; `mypy backend`
  sin problemas (58 archivos); `makemigrations --check --dry-run` sin cambios; `pytest --cov` 156
  pasan, coverage total 91.7 % (app `campanias` 96.7 %); frontend `format:check`/`lint`/`typecheck`
  OK, `test:coverage` 56 pasan (líneas 89.3 %, sentencias 87.3 %), `build` OK; `pre-commit
  run --all-files` todo en verde (gitleaks sin hallazgos). Esperando a Juan Diego.
- Gate 3 (PR): #15 (mergeado a develop el 2026-10-19).
