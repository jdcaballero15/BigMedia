# Unidad: Ajuste de datos de ejemplo para demos

- **Estado:** en revisión · **Épica:** — (unidad técnica) · **App dueña:** `usuarios` (comando) + `infra`
- **Origen:** pedido de Gonza del 23/10/2026 (mostrar el sistema en staging) · **Rama:** `chore/infra-datos-ejemplo-demo`

## Objetivo

Que staging tenga datos suficientes en todas las pantallas para hacer una demo: inventario,
catálogos, clientes, marcas, rubros, campañas, reservas, costos y márgenes, disponibilidad,
calendario, panel, reportes (ocupación, ingresos, por rubro) y auditoría. Ajusta
`cargar_datos_ejemplo` de la unidad `entornos`, ya mergeada.

## Decisiones de diseño (mi criterio — corregir acá si hace falta)

1. **Se amplía el mismo comando.** Sigue corriendo al arrancar staging (`backend/arrancar.sh`) y
   negándose a correr en producción.
2. **Segundo bloque con su propio centinela.** Staging ya tiene el primer lote (centinela «Agencia
   Norte»), así que el comando no volvería a cargar. Se agrega un bloque «demo» con el centinela
   «Distribuidora Andina»: si no existe, se carga, sin tocar ni duplicar el primer lote. En una base
   nueva corren los dos. Las dos cosas siguen siendo idempotentes.
3. **Volumen:**
   - 4 proveedores (impresión, fijación, mantenimiento LED, dueño de estructuras) asignados a carteles.
   - 6 rubros, asignados a todas las marcas, también a las 3 del primer lote si no tienen rubro.
   - 16 carteles más en los 7 formatos y en 6 departamentos, con estados variados (activos, uno en
     mantenimiento, uno apagado, uno de baja) y tarifas distintas.
   - 6 clientes más (agencias y directos) y 10 marcas.
   - 10 campañas en todos los estados (cotizada, confirmada, cancelada, perdida).
   - Unas 25 reservas en todos los estados, desde 5 meses atrás hasta 3 meses adelante, para que el
     calendario, la ocupación y los reportes por mes tengan datos.
   - Costos (impresión, fijación, otro) en unas 15 reservas, con proveedor, para que se vean
     márgenes positivos y alguno negativo.
4. **Disponibilidad respetada.** Cada reserva que bloquea cupo pasa por
   `reservas.services.validar_disponibilidad` antes de guardarse, así la demo no muestra sobreventa.
5. **Auditoría con su servicio.** Se registran unos 8 cambios con
   `auditoria.services.registrar_cambios` (tarifa de un cartel, estado de una reserva, fechas de una
   campaña), atribuidos a los usuarios de demo, para que la pantalla de auditoría tenga contenido.
6. **Usuarios de demo, sin contraseña en el código.** Se crean `demo-operativo` (Operativo),
   `demo-gerencia` (Operativo + Gerencia) y `demo-lectura` (Lectura), así se pueden mostrar los
   roles de HU-004. La contraseña sale de una variable nueva, `DJANGO_DEMO_PASSWORD`. Sin la
   variable no se crean usuarios y la auditoría queda con origen `sistema`. Se agrega a
   `render.yaml` (staging, `sync: false`) y a `backend/.env.example`.
7. **Todo inventado** (regla 6): nombres de fantasía, sin CUIT, correos `@example.com`, sin
   teléfonos.
8. **Fechas relativas al día en que corre**, como el primer lote. En staging se cargan una sola vez,
   así que con el tiempo van quedando en el pasado; para refrescarlas se recrea la base.
9. **Arquitectura:** el comando vive en `usuarios` y ya importaba modelos de `inventario`,
   `clientes`, `campanias` y `reservas`, algo que la tabla de dependencias no permite. Sumarle
   `costos` y `auditoria` agranda esa excepción. Lo dejo donde está para no ampliar el alcance; si
   preferís, en esta unidad lo muevo a `config/management/commands/` (no es una app de negocio).

## Cambios

- `backend/apps/usuarios/management/commands/_datos_demo.py` (nuevo): el lote demo (tablas de datos y
  funciones chicas). Django no lo toma como comando porque empieza con `_`.
- `backend/apps/usuarios/management/commands/cargar_datos_ejemplo.py`: después del primer lote llama
  a `_datos_demo.cargar()`.
- `backend/tests/test_render_blueprint.py`: `DJANGO_DEMO_PASSWORD` solo en staging y sin valor en Git.
- `render.yaml`: `DJANGO_DEMO_PASSWORD` en el servicio de staging (`sync: false`).
- `backend/.env.example`: la variable nueva, documentada.
- `docs/operacion/despliegue-render.md`: qué carga staging y cómo se entra con los usuarios de demo.

## Migraciones

Ninguna.

## Reglas provisorias que se usan

Ninguna.

## Cómo se prueba

En `backend/tests/test_datos_ejemplo.py`, contra PostgreSQL:

- `test_carga_demo_llena_todas_las_pantallas`: hay carteles, proveedores, rubros, clientes, marcas,
  campañas, reservas en cada estado, costos y registros de auditoría.
- `test_carga_demo_respeta_la_capacidad_de_cada_cartel`: ningún día supera la capacidad.
- `test_carga_demo_sobre_primer_lote_existente_agrega_sin_duplicar`: es el caso de staging hoy.
- `test_carga_demo_es_idempotente`.
- `test_carga_demo_con_clave_crea_usuarios_con_su_rol` y
  `test_carga_demo_sin_clave_no_crea_usuarios`.
- Los tres tests actuales siguen pasando.
- Verificación completa de backend (Definition of Done). No toca el frontend.

Después del merge a `develop`: antes del deploy hay que cargar `DJANGO_DEMO_PASSWORD` en Render
(staging). Después del deploy, revisar en staging que cada pantalla tenga datos.

## Registro de gates

- Gate 1 (plan): 2026-10-23 — aprobado por Gonza tal cual (con usuarios de demo y
  `DJANGO_DEMO_PASSWORD`; el comando queda en `usuarios`).
- Gate 2 (verificación): 2026-10-23 — Backend: `ruff format --check` (104 archivos), `ruff check`,
  `mypy` (104, sin errores), `makemigrations --check` sin cambios y `pytest --cov` 361 pasan
  (95.05 %; `_datos_demo.py` 98 %). `pre-commit run --all-files` con gitleaks pasa. Frontend sin
  cambios. Aprobado por Gonza el mismo día.
- Gate 3 (PR): _pendiente_
