# Despliegue de Big Media en Render

Hoy `render.yaml` usa el **plan gratis** de Render (servicio web y PostgreSQL), para que el equipo y
Seba puedan ver el sistema funcionando mientras se valida. La presencia del archivo en Git no crea
recursos por sí sola: se crean al aplicar el Blueprint desde el panel de Render.

## Límites del plan gratis

- **La web se duerme** después de 15 minutos sin tráfico. La primera visita después tarda cerca de un
  minuto en responder.
- **La base gratis vence a los 30 días** de creada. Hay 14 días de gracia para pasarla a un plan pago;
  después Render la borra con todos sus datos. Solo se permite una base gratis por workspace.
- La base gratis tiene 1 GB fijo y **no tiene copias de seguridad**.
- No hay consola (Shell) ni comando previo al deploy. Por eso la imagen migra la base y crea el
  primer administrador en cada arranque (`backend/arrancar.sh`).
- **No cargar el inventario real** en el plan gratis. Usarlo para mostrar y probar; pasar al plan pago
  antes de que Seba cargue datos que no se pueden perder.

## Crear los servicios

1. La rama `main` tiene que tener el CI en verde: Render solo despliega commits de `main` cuyos checks
   pasaron (`autoDeployTrigger: checksPass`).
2. En Render, abrir **Blueprints → New Blueprint Instance**, conectar GitHub y elegir
   `jdcaballero15/BigMedia`, rama `main`.
3. Render pide dos valores que no están en Git:
   - `DJANGO_SUPERUSER_USERNAME`: el usuario del primer administrador.
   - `DJANGO_SUPERUSER_PASSWORD`: una contraseña larga y única. No la guardes en el repositorio ni la
     mandes por chat.
4. Revisar que los dos recursos (`bigmedia-web` y `bigmedia-db`) digan **Free** y aplicar el Blueprint.
5. Esperar el build. En **Logs** tienen que aparecer las migraciones, `Administrador <usuario> creado.`
   y `Listening at`. El chequeo `/api/health/` debe dar `{"status":"ok"}`.
6. Anotar la URL que asigna Render (por ejemplo `https://bigmedia-web.onrender.com`).

`DATABASE_URL` viene de la URL interna de `bigmedia-db` y `DJANGO_SECRET_KEY` la genera Render.
Nunca copiar esos valores a Git ni a mensajes.

El comando `asegurar_admin` no hace nada si el usuario ya existe, así que cambiar la contraseña desde
`/admin/` es seguro: un nuevo deploy no la pisa.

## Primeros pasos en producción

1. Abrir la URL: debe cargar la app por HTTPS. `/api/health/` debe responder `{"status":"ok"}`.
2. Entrar a `/admin/` con el administrador. Crear una cuenta por persona (Seba, socios), sin cuentas
   compartidas, y asignar el grupo **Operativo** a quien vaya a cargar o editar carteles.
3. Probar con esas cuentas: inicio y cierre de sesión, lectura de carteles, edición con permiso y
   rechazo de edición sin permiso.

## Pasar al plan pago

Hacerlo antes de los 30 días si se van a conservar los datos, y siempre antes de cargar el
inventario real.

1. En el panel de Render, cambiar `bigmedia-db` a un plan pago (por ejemplo `basic-256mb`) y
   `bigmedia-web` a `starter`. Revisar el precio en el panel antes de confirmar.
2. En el mismo PR que actualiza `render.yaml` con esos planes, se puede volver a usar
   `preDeployCommand: python manage.py migrate --noinput`. El arranque de la imagen sigue migrando y no
   molesta: si no hay migraciones pendientes, no hace nada.
3. Activar y verificar las copias de seguridad según la sección siguiente.

## Verificar antes de ingresar datos reales (plan pago)

1. Abrir la URL raíz: debe cargar React por HTTPS. `/static/assets/` debe responder CSS y JavaScript; `/api/health/` debe devolver `{"status":"ok"}`. Un 503 indica que la API no puede conectar con PostgreSQL.
2. En **Shell** del servicio web ejecutar `python manage.py check --deploy`. Las advertencias `security.W005` y `security.W021` son deliberadas mientras se use el subdominio `onrender.com`: Big Media no controla todos sus subdominios y por eso no habilitamos HSTS para subdominios ni preload. Investigar cualquier otra advertencia.
3. Ejecutar `python manage.py showmigrations` en Shell y comprobar que las migraciones están aplicadas. Repetir tras un nuevo despliegue para confirmar que la base persiste.
4. El primer administrador ya existe (lo crea `asegurar_admin` al arrancar). Ingresar a `/admin/` con él y confirmar que un usuario no autenticado no puede administrar datos.
5. Cuando el PR de inventario esté integrado, crear cuentas separadas para Seba y Ale, asignarles el grupo **Operativo** y probar: inicio/cierre de sesión, lectura de carteles, edición con permiso y rechazo de edición sin permiso. No usar una cuenta compartida.
6. Cargar un cartel real pequeño sólo después de verificar la restauración. Confirmar que se conserva tras un nuevo despliegue.

## Recuperación y copias

- PostgreSQL pago en el workspace Hobby de Render tiene recuperación a un punto anterior de **3 días**. Comprobar en **bigmedia-db → Recovery** que esté disponible. [Documentación de Render](https://render.com/docs/postgresql-backups).
- Antes de usar el sistema como fuente de datos real, iniciar una restauración de prueba hacia **una nueva instancia**. Comprobar allí las tablas y registros de `django_migrations`; no cambiar la conexión de producción para esta prueba. La instancia temporal puede generar un cargo hasta que se elimine.
- Antes de una migración de riesgo, crear una exportación lógica desde **Recovery → Create export**, descargarla y guardarla en almacenamiento privado bajo control de Big Media. Render conserva esas exportaciones en su panel durante siete días; descargar una copia para retención mayor.
- Si se necesita recuperar producción, crear una instancia restaurada, verificar sus datos, cambiar `DATABASE_URL` del servicio web hacia ella y comprobar salud e inicio de sesión antes de retirar la instancia anterior. Un rollback de código **no revierte** una migración de base.
- Si Big Media necesita conservar copias por más de tres días de manera continua, definir y probar una copia externa periódica antes de depender exclusivamente del sistema.

## Operación diaria

- Revisar **Deploys** y **Logs** cuando falle un build, migración o chequeo de salud.
- Vigilar uso de disco, factura y disponibilidad de recuperación en el panel.
- Integrar cambios solo por PR según GitFlow ([gestión de configuración](../gestion-de-configuracion.md)): rama de trabajo → PR a `develop`; `main` solo recibe releases desde `develop` y hotfixes; CI prueba backend, frontend y construcción de la imagen antes del despliegue automático.
- Mantener datos reales fuera de bases de desarrollo y pruebas locales. El entorno local usa `.env` y Docker Compose según [desarrollo local](desarrollo-local.md).
