# Unidad: Reporte de ingresos por cliente y marca

- **Estado:** en curso · **Épica:** E8 Reportes y paneles · **App dueña:** `facturacion` (nueva)
- **Origen:** HU-049 · **Rama:** `feature/facturacion-reporte-ingresos`

## Objetivo

Dar a gerencia la facturación por período con el desglose cliente (agencia) → marca, ordenable como
ranking, para saber quién genera más ingresos (HU-049). El ingreso de cada reserva se reparte en el
tiempo según HU-051 (`reservas.services.reparto_por_mes`), de modo que la facturación mensual y anual
no quede distorsionada por reservas de varios meses.

## Decisiones de diseño (mi criterio — corregir acá si hace falta)

1. **App dueña `facturacion` (nueva).** El reporte cruza reserva → campaña → marca → cliente, y
   `reservas` no puede importar `clientes` (solo `inventario`, `campanias`). La única app autorizada a
   importar `reservas` + `campanias` + `clientes` es `facturacion` (tabla de arquitectura). Se crea
   `backend/apps/facturacion/` **sin modelos** (reporte de solo lectura): importes, cierre y
   exportación llegan en unidades posteriores. No hace falta ADR: la app ya está en la arquitectura.
2. **Alcance backend.** Esta unidad entrega el servicio de agregación + el endpoint, con tests. La
   pantalla del reporte (expandir agencia, ordenar ranking, filtrar período) va en una unidad de
   frontend aparte (`reporte-ingresos-frontend`), por tamaño y para revisarlo acotado.
3. **Quién factura:** se agrupa por `campania.cliente_factura` (RN-014: el cliente propio de la
   campaña si está; si no, el de la marca). Reservas sin cliente resoluble caen en un bucket
   "Sin cliente"; marca nula, en "Sin marca".
4. **Qué reservas cuentan:** las que ocupan cupo, es decir no canceladas
   (`Reserva.ESTADOS_QUE_OCUPAN`: pendiente, confirmada, finalizada). Las canceladas no facturan.
5. **Permisos:** solo lectura con sesión (se reutiliza `LecturaConSesionEdicionOperativo`). El cierre
   de ingresos a un grupo "Gerencia" (dato sensible) queda para cuando se defina el permiso de ver
   ingresos (atado a HU-052); hoy ese grupo no existe. **Marcado como decisión a confirmar.**
6. **Comparativo interanual:** fuera de alcance por ahora (el criterio dice "cuando haya historia
   suficiente"); la exportación es HU-052, otra unidad.

## Cambios

- **`backend/apps/facturacion/`** (app nueva, sin modelos): `apps.py`, `__init__.py`, `services.py`,
  `views.py`, `urls.py`.
- `facturacion/services.py`: `reporte_ingresos(desde, hasta)` →
  - toma las reservas no canceladas que se solapan con `[desde, hasta]`, con
    `select_related("campania__marca__cliente", "campania__cliente_facturacion")`;
  - por cada reserva usa `reparto_por_mes` y se queda con los montos de los meses dentro del período;
  - acumula por cliente (agencia) y, dentro, por marca, con subtotal por mes y total;
  - devuelve `{ periodos: [{mes, etiqueta}], clientes: [{cliente, nombre, total, por_mes,
    marcas: [{marca, nombre, total, por_mes}]}], total }`, con clientes y marcas **ordenados por
    total descendente** (ranking). Importes con `Decimal`.
- `facturacion/views.py`: `IngresosView` (solo lectura) `GET /api/facturacion/ingresos/`, parámetros
  `desde` y `hasta` en `AAAA-MM` (por defecto: del 1 de enero al 31 de diciembre del año actual, para
  que "anual" funcione de entrada). Valida formato y `desde <= hasta` → 400.
- `facturacion/urls.py` + `config/urls.py`: `path("api/facturacion/", include("apps.facturacion.urls"))`.
- `config/settings.py`: agregar `"apps.facturacion"` a `INSTALLED_APPS`.

### Reglas (HU-049)

- Desglose por la cadena reserva → campaña → marca → cliente (`cliente_factura`, RN-014).
- Los totales cuadran: `total` del cliente = suma de sus marcas = suma de sus meses; `total` global =
  suma de los clientes. El reparto por mes (HU-051) ya garantiza la suma al centavo por reserva.

## Migraciones

Ninguna (la app no tiene modelos).

## Reglas que se usan

- **RN-014** (cliente que factura): se **consume** `campania.cliente_factura`, ya implementado en
  `campanias`. No cambia su "Dónde vive"; no se toca `reglas-de-negocio.md`. El test del caso lleva
  `@pytest.mark.regla("RN-014")`.

## Cómo se prueba

- Backend (`backend/tests/test_reporte_ingresos.py`, PostgreSQL real):
  - un cliente con dos marcas: cada marca muestra su ingreso y el total del cliente = suma de las
    marcas (HU-049 criterio 1).
  - ranking de clientes y de marcas ordenado por total desc; los totales cuadran contra la suma
    manual (criterio 2).
  - filtro por período: una reserva de sep a nov, pidiendo solo octubre, aporta únicamente el monto de
    octubre del reparto (criterio 3).
  - una reserva cancelada no suma; `cliente_facturacion` propio de la campaña reemplaza al de la marca
    (RN-014); `desde > hasta` y formato inválido → 400; anónimo → 401/403.

## Registro de gates

- Gate 1 (plan): 2026-10-20 — aprobado (alcance backend; permiso de solo lectura con sesión, cierre a
  "Gerencia" diferido a HU-052).
- Gate 2 (verificación): 2026-10-20 — `ruff format --check`, `ruff check`, `mypy backend` (86
  archivos), `makemigrations --check` y gitleaks en verde; `pytest --cov` 247 pasan, cobertura total
  94.63 % (umbral 80 %). Frontend no aplica (unidad sin frontend).
- Gate 3 (PR): —
