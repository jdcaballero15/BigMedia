# Arquitectura

Cómo está organizado Big Media y qué puede depender de qué. Las reglas absolutas viven en [`CLAUDE.md`](../CLAUDE.md); la decisión de fondo, en [ADR-0001](adr/0001-estructura-del-repositorio.md).

## 1. Estilo

- **Monolito modular.** Una API Django + Django REST Framework y una sola base PostgreSQL 17. Cada área de negocio es una app de Django en `backend/apps/<app>/`.
- **Frontend React 19 + Vite + TypeScript** en `frontend/`. En producción lo sirve la misma imagen que la API: Django entrega la página compilada y sus archivos estáticos, y React llama a `/api/` en el mismo origen (resumen de [despliegue en Render](operacion/despliegue-render.md)).
- **Producción:** Render despliega `main` con `autoDeployTrigger: checksPass`, es decir, solo cuando el CI está en verde. `develop` integra y solo corre CI.
- **Referencia, no copia.** La organización se inspiró en el repositorio [CheatSheet](https://github.com/cheatsheet12/CheatSheet) (monorepo, documentación, controles); sus módulos y tecnologías responden a otro negocio. Django y Vite permanecen: esta guía trata de **organización**, no de migrar de tecnología.
- **No se crean carpetas vacías** para funciones futuras ni carpetas nuevas en la raíz sin un ADR aprobado.

## 2. Árbol del repositorio

```text
bigMedia/
├── CLAUDE.md                       # constitución normativa
├── README.md                       # qué es, cómo arrancar, enlaces a docs/
├── pyproject.toml                  # ruff, mypy, pytest y coverage para todo el Python
├── requirements-dev.txt            # herramientas con versión fija
├── .pre-commit-config.yaml
├── .gitleaks.toml
├── compose.yaml                    # Postgres local; lee backend/.env
├── Dockerfile, .dockerignore, render.yaml   # sin cambios de forma
├── .github/
│   ├── workflows/ci.yml
│   ├── pull_request_template.md
│   └── ISSUE_TEMPLATE/pedido.yml
├── .claude/
│   └── aidlc/
│       ├── AIDLC.md
│       └── workflow.md
├── backend/
│   ├── pyproject.toml              # solo empaquetado y dependencias de la aplicación
│   ├── .env.example
│   ├── manage.py
│   ├── config/
│   ├── apps/<app>/
│   └── tests/
│       └── README.md
├── frontend/
│   ├── .prettierrc.json
│   ├── .oxlintrc.json
│   ├── package.json                # scripts typecheck, format:check, test:coverage
│   └── src/{app,features/<app>,shared}/
└── docs/
    ├── README.md
    ├── arquitectura.md
    ├── estandares-de-codigo.md
    ├── gestion-de-configuracion.md
    ├── adr/
    ├── operacion/
    └── aidlc/
        ├── inputs/                 # historias, registro de cambios, importacion/, ux/
        ├── reglas-de-negocio.md
        ├── roadmap.md
        ├── units.md
        └── units/<unidad>.md
```

Qué va dónde:

| Ubicación | Qué contiene |
| --- | --- |
| Raíz | Lo que gobierna ambos lados: `pyproject.toml` (ruff, mypy, pytest, coverage), `requirements-dev.txt`, `.pre-commit-config.yaml`, `.gitleaks.toml`, `compose.yaml`, `Dockerfile`, `render.yaml`, `CLAUDE.md`, `README.md`, `docs/`, `.claude/`, `.github/`. |
| `backend/` | API Django: `config/` (settings, URLs y lo compartido entre apps: `permisos.py` con el permiso "lee cualquiera con sesión, edita Operativo" y `texto.py` con la normalización para buscar sin tildes), `apps/<app>/`, `tests/`, `manage.py`, `pyproject.toml` (empaquetado) y `.env.example`. |
| `frontend/` | Web React: `package.json`, configuración de Prettier, oxlint, TypeScript y Vite, y `src/`. |
| `docs/` | Documentación. Los insumos y el plan de trabajo viven en `docs/aidlc/`. |

## 3. Apps del backend

Los límites vienen de la unidad [`base-del-repositorio`](aidlc/units/base-del-repositorio.md).

| App | Responsabilidad | Riesgo dominante | Estado |
| --- | --- | --- | --- |
| `usuarios` | Cuentas, sesión y permisos. | Acceso no autorizado a datos o acciones. | implementada |
| `inventario` | Formatos, proveedores, zonas, carteles, estados físicos y capacidad. | Capacidad mal cargada, que luego rompe la disponibilidad. | implementada |
| `clientes` | Clientes pagadores, marcas y contactos. | Datos personales mal tratados. | implementada |
| `campanias` | Campañas, posiciones solicitadas por formato e interacciones comerciales (viven acá porque pueden llevar campaña). | Posiciones inconsistentes con lo vendido. | implementada |
| `reservas` | Reservas, disponibilidad, confirmación, cancelación y carga masiva. Toda vía de entrada usa el mismo servicio de confirmación. | Sobreventa de un cartel. | implementada (falta la carga masiva, E10) |
| `costos` | Costos asociados a reservas e ítems de facturación, evitando contabilizarlos dos veces. | Contabilizar un costo dos veces. | implementada (costos de reservas) |
| `facturacion` | Ítems, cálculo de importes, cierre mensual y exportación XLSX. | Importes y cierre mensual incorrectos. | planificada |
| `auditoria` | Registro inmutable de cambios relevantes. | Pérdida de inmutabilidad del registro. | implementada |

## 4. Dependencias permitidas entre apps

Una app no importa modelos de otra fuera de esta tabla. Cualquier app puede importar de `django.contrib.auth` y de `config` (nivel de proyecto).

| App | Puede importar de |
| --- | --- |
| `inventario` | — |
| `clientes` | — |
| `usuarios` | — |
| `campanias` | `clientes`, `inventario` ([ADR-0007](adr/0007-campanias-importa-de-inventario.md)) |
| `reservas` | `inventario`, `campanias` |
| `costos` | `reservas`, `inventario` |
| `facturacion` | `campanias`, `reservas`, `costos`, `clientes` |
| `auditoria` | ninguna: las demás le escriben a través de su servicio |

Esto **se revisa en el PR**; ninguna herramienta lo verifica (ver [ADR-0001](adr/0001-estructura-del-repositorio.md) para la alternativa descartada). Si una dependencia nueva parece necesaria, se discute antes de escribirla y, si cambia esta tabla, se actualiza acá en el mismo PR.

## 5. Regla crítica de disponibilidad

La capacidad se toma del cartel, no del formato. Para cada confirmación se verifica la ocupación máxima **en cada tramo del rango solicitado**, no solo el número total de reservas que tocan el rango. Las confirmaciones del mismo cartel se serializan dentro de una transacción de PostgreSQL con bloqueo de fila; las de carteles diferentes pueden avanzar en paralelo. La configuración del día de borde y de las reservas pendientes la lee el servicio de disponibilidad.

Las reglas de negocio que la condicionan están en el catálogo [`reglas-de-negocio.md`](aidlc/reglas-de-negocio.md):

- **RN-001**: día límite entre reservas.
- **RN-002**: si una reserva Pendiente bloquea a otras.
- **RN-003**: cómo se cuentan los cupos dentro de un rango.

Las 16 situaciones del anexo de HU-031 y las pruebas de concurrencia de HU-034 son criterios obligatorios antes de dar por terminada la app `reservas`. El mecanismo exacto de bloqueo y la representación de los rangos se cierran en la unidad de esa app.

## 6. Frontend

```text
frontend/src/
├── app/                # arranque, rutas y sesión
├── features/<app>/     # pantallas y lógica de cada área, con los mismos nombres de app
└── shared/             # cliente HTTP y UI común
```

- `features/<app>/` espeja a las apps del backend. Una feature no importa de otra: lo común sube a `shared/`.
- **El frontend no decide reglas de negocio.** Por ejemplo, nunca decide si una reserva puede confirmarse: lo decide el servidor y lo protege PostgreSQL.
- Se agregan carpetas de feature cuando la app correspondiente se implementa.
