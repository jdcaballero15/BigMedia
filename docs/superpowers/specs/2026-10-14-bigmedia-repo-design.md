# Big Media — diseño del repositorio

Estado: propuesta para revisión, 14 de octubre de 2026.

## Objetivo

Crear una base de desarrollo para el sistema descrito en *Historias de usuario - Sistema de reservas OOH (desarrollo a medida).md*. La primera entrega deja un repositorio reproducible y preparado para implementar las 68 historias por etapas. El núcleo del producto será impedir reservas confirmadas que excedan la capacidad de un cartel en cualquier día del período.

## Enfoque

Un monorepo con una aplicación web React + TypeScript, una API Django REST Framework y PostgreSQL. Se usará un monolito modular: una sola API y una sola base de datos, con módulos separados por área de negocio. Power BI consultará vistas SQL de lectura cuando se implementen los reportes.

La carpeta local será `C:\Users\Juan Diego\Desktop\MendoData\proyectos\bigMedia`, vinculada a `https://github.com/jdcaballero15/BigMedia`. El documento de historias se conservará como fuente de requisitos. El PDF de la orden de compra existente es material privado de referencia y no se incorporará al control de versiones.

## Estructura propuesta

```text
bigMedia/
├── README.md
├── .gitignore
├── .env.example
├── compose.yaml
├── .vscode/
│   ├── extensions.json
│   └── settings.json
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── app/                   # arranque, rutas y sesión
│   │   ├── features/              # pantallas y lógica por área
│   │   │   ├── inventario/
│   │   │   ├── clientes/
│   │   │   ├── campanias/
│   │   │   ├── reservas/
│   │   │   ├── disponibilidad/
│   │   │   ├── facturacion/
│   │   │   └── reportes/
│   │   └── shared/                # UI, tipos y cliente HTTP comunes
│   └── tests/
├── backend/
│   ├── manage.py
│   ├── pyproject.toml
│   ├── config/                    # settings, URLs y ASGI/WSGI
│   ├── apps/
│   │   ├── usuarios/
│   │   ├── inventario/
│   │   ├── clientes/
│   │   ├── campanias/
│   │   ├── reservas/
│   │   ├── costos/
│   │   ├── facturacion/
│   │   └── auditoria/
│   └── tests/                     # integración y concurrencia
├── analytics/
│   ├── sql/
│   └── powerbi/
├── docs/
│   ├── requisitos/
│   ├── arquitectura/
│   ├── decisiones/
│   └── operacion/
└── scripts/
```

Las carpetas vacías se crearán cuando tengan contenido real. No se crearán modelos, vistas o endpoints ficticios solo para llenar la estructura.

## Límites entre módulos

- `inventario`: formatos, proveedores, zonas, carteles, estados físicos y capacidad.
- `clientes`: clientes pagadores, marcas, contactos e interacciones.
- `campanias`: campañas y posiciones solicitadas por formato.
- `reservas`: reservas, disponibilidad, confirmación, cancelación y carga masiva. Toda vía de entrada usará el mismo servicio de confirmación.
- `costos`: costos asociados a reservas e ítems de facturación, evitando contabilizarlos dos veces.
- `facturacion`: ítems, cálculo de importes, cierre mensual y exportación XLSX.
- `auditoria`: registro inmutable de cambios relevantes.

El frontend refleja estos límites en `features/`, pero no decide si una reserva puede confirmarse. Esa regla se ejecuta en el servidor y se protege en PostgreSQL.

## Regla crítica de disponibilidad

La capacidad se toma del cartel, no del formato. Para cada confirmación se verificará la ocupación máxima **en cada tramo del rango solicitado**, no solo el número total de reservas que tocan el rango. Las confirmaciones del mismo cartel se serializarán dentro de una transacción; las de carteles diferentes podrán avanzar en paralelo. La configuración del día de borde y de las reservas pendientes será leída por el servicio de disponibilidad. Las 16 situaciones del anexo de HU-031 y las pruebas de concurrencia de HU-034 serán criterios obligatorios antes de considerar terminada esa etapa.

El mecanismo exacto de bloqueo y la representación de los rangos se cerrarán en la especificación del módulo de reservas, después de confirmar las reglas de borde y cupos con Seba. El diseño del repositorio no presupone que cada cupo sea un slot físico identificable.

## Primera entrega del repositorio

1. Vincular la carpeta al repositorio remoto sin perder los archivos existentes.
2. Crear README, `.gitignore`, ejemplo de variables de entorno y configuración de VS Code.
3. Inicializar Vite + React + TypeScript y Django + Django REST Framework.
4. Configurar PostgreSQL local mediante Compose y migraciones iniciales de Django.
5. Añadir verificaciones básicas de arranque y documentación para instalar, ejecutar y probar el proyecto.
6. Mantener el PDF existente fuera de los commits y registrar la procedencia del documento de historias.

Esta entrega no incluye todavía las 68 historias funcionales. Después vendrán, en orden: seguridad; inventario y clientes; campañas; reservas y disponibilidad; operaciones masivas; costos y facturación; reportes.

## Decisiones abiertas

Las 12 decisiones de negocio listadas al final del documento de historias se documentarán en `docs/decisiones/`. Para la primera entrega del repositorio no bloquean el trabajo. Antes de implementar el motor de reservas deben resolverse, o aplicarse explícitamente los valores provisorios del documento, el día de borde, el efecto de las pendientes y la interpretación de la capacidad de LED y séxtuples.

## Criterios de aceptación de la primera entrega

- El repositorio se abre desde su raíz en VS Code.
- Una persona nueva puede levantar PostgreSQL, API y frontend siguiendo el README.
- Las migraciones se ejecutan en una base vacía.
- Frontend y backend pasan sus verificaciones iniciales.
- No se versionan secretos, datos personales reales ni el PDF privado existente.
- El directorio conserva el documento de historias y el vínculo con el remoto indicado.
