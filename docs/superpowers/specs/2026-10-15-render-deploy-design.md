# Despliegue inicial de Big Media en Render

## Objetivo

Publicar el sistema para que Seba y Ale lo usen con datos reales de Big Media, desde una URL HTTPS, con una base PostgreSQL persistente y un proceso de despliegue que respete los Pull Requests. Esta entrega prepara la infraestructura y el procedimiento de puesta en marcha. El módulo de inventario se habilita cuando su PR se integre; campañas y reservas siguen fuera del alcance funcional actual.

## Decisión

Usar un servicio web pago y una base PostgreSQL paga de Render, en la misma región. El servicio web ejecutará Django y servirá la aplicación React compilada desde el mismo origen. Render desplegará la rama `main` después de cada integración aprobada por PR. La primera URL será la asignada por Render; un dominio propio puede añadirse más adelante.

Se eligió esta opción por su operación en un solo proveedor, conexión privada entre la aplicación y la base, TLS administrado y recuperación a un punto anterior de PostgreSQL. La alternativa Render + Neon requiere dos cuentas y una conexión a la base por Internet; puede evaluarse si cambian los requisitos de recuperación o costos. Los planes gratuitos no se usarán para datos reales.

## Arquitectura y flujo

1. El navegador solicita la URL HTTPS de Render. Django devuelve la página React compilada y sus archivos estáticos.
2. React llama a `/api/` en el mismo origen. Django mantiene las sesiones y la protección CSRF existentes; `/admin/` queda disponible sólo para usuarios administrativos.
3. Django accede a PostgreSQL mediante la cadena de conexión privada que entrega Render. La base no se expone públicamente.
4. `/api/health/` comprueba la conexión a la base y permite a Render detectar una instancia que no puede atender solicitudes.
5. El build produce una imagen reproducible con Node para compilar React y Python para ejecutar Django con un servidor WSGI de producción. Los archivos estáticos se reúnen durante el build.

No se crean datos de ejemplo en producción. La carga real comienza después de verificar el despliegue y las cuentas de usuario.

## Configuración y seguridad

- El repositorio contendrá la definición de Render y el código de despliegue, nunca claves, contraseñas ni datos reales.
- `DJANGO_SECRET_KEY` se generará como secreto del servicio. `DATABASE_URL` vendrá de la base administrada. `DJANGO_DEBUG` será falso.
- Django aceptará el host asignado por Render, confiará en el encabezado HTTPS del proxy de Render y usará cookies de sesión y CSRF seguras. La configuración local seguirá funcionando con `.env` y Docker Compose.
- Sólo los usuarios creados por un administrador podrán iniciar sesión. Se crearán cuentas individuales para Seba y Ale y se asignarán sus permisos de inventario. No habrá registro público.
- Se ejecutará `manage.py check --deploy` antes de la puesta en marcha. Se comprobará que las rutas de API y administración sigan protegidas.

## Publicación y migraciones

El PR incorporará la configuración de Render, el empaquetado de React y Django, las variables de entorno necesarias y una guía operativa. El build y las pruebas se ejecutarán antes de integrar el PR. Render construirá la imagen desde `main` y ejecutará las migraciones de Django como paso previo a activar la nueva versión. Si el build o la migración fallan, la nueva versión no se publicará; el error deberá quedar visible en los logs de Render. Los cambios de esquema futuros deberán conservar compatibilidad con la versión anterior durante el cambio de instancia.

La creación del servicio y de la base paga, la conexión de GitHub con Render y la carga de datos reales requieren un paso operativo posterior con acceso a la cuenta de Big Media y autorización del gasto. Ninguna integración del PR creará recursos pagos por sí sola.

## Recuperación y operación

La base PostgreSQL paga de Render ofrece recuperación a un punto anterior. En el plan Hobby, la ventana documentada es de tres días. Antes de cargar datos reales, se confirmará en el panel que la recuperación esté activa y se hará una restauración de prueba en una base separada. La guía operativa incluirá cómo verificar salud, revisar logs, crear usuarios, restaurar y exportar datos antes de una migración de riesgo. Si Big Media necesita una retención mayor a tres días, se definirá almacenamiento adicional de copias antes de usar el sistema como fuente única de datos.

## Verificación y criterios de aceptación

- La imagen se construye desde cero y el frontend compilado carga en la ruta raíz.
- Las pruebas existentes de frontend y backend pasan, incluida la integración con PostgreSQL donde esté disponible.
- `check --deploy` no reporta problemas pendientes de seguridad relevantes para esta configuración.
- En una instalación de prueba, HTTPS responde, `/api/health/` informa conexión a la base, el inicio y cierre de sesión funcionan y una persona sin permiso no puede modificar inventario.
- Las migraciones se ejecutan sin cargar datos ficticios y los datos persisten después de un nuevo despliegue.
- Se verifica una recuperación de PostgreSQL antes de introducir datos reales.

## Fuera de alcance

Esta entrega no implementa reservas, campañas, disponibilidad, reportes, carga masiva de inventario, dominio propio ni correos transaccionales. Tampoco importa datos reales automáticamente.
