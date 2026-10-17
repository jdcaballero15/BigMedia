# Despliegue de Big Media en Render

Esta guía prepara una instalación **operativa con datos reales**. El archivo `render.yaml` crea un servicio web pago y PostgreSQL pago cuando se aplica como Blueprint. La presencia del archivo en Git no crea ni factura recursos por sí sola.

## Antes de aplicar el Blueprint

1. Integrar por PR la configuración de despliegue y el módulo de inventario. La rama `main` debe tener CI verde. Sin el PR de inventario, la web publicada sólo muestra la base de desarrollo.
2. Crear o elegir una cuenta de Render controlada por Big Media, conectar el repositorio de GitHub y configurar un medio de pago. Revisar precios en el panel antes de aplicar.
3. Confirmar que `render.yaml` declara el servicio `0.5c-512mb`, PostgreSQL `0.1c-256mb` y 5 GB iniciales de disco. Con los precios consultados en octubre de 2026, la estimación es aproximadamente **USD 14,50/mes** (web USD 7 + base USD 6 + disco USD 1,50), antes de consumo adicional de ancho de banda, almacenamiento o minutos de build. El disco puede crecer automáticamente y aumentar el costo. [Precios de Render](https://render.com/pricing), [planes de cómputo](https://render.com/docs/compute-plans).
4. No cargar datos reales hasta terminar la verificación y la prueba de restauración de abajo.

## Crear los servicios

1. En Render, abrir **Blueprints → New Blueprint Instance** y seleccionar `jdcaballero15/BigMedia`, rama `main`.
2. Revisar los dos recursos propuestos y el cargo estimado; aplicar el Blueprint sólo con autorización del gasto.
3. Confirmar que el servicio y la base se crearon en `virginia`, y que la base no tiene direcciones IP externas permitidas (`ipAllowList: []`). `DATABASE_URL` debe venir de la URL interna de `bigmedia-db`; `DJANGO_SECRET_KEY` se genera en Render. Nunca copiar esos valores a Git ni a mensajes.
4. Esperar el build, el comando previo `python manage.py migrate --noinput` y el chequeo `/api/health/`. El servicio despliega `main` sólo cuando pasan los checks de GitHub. Si la migración falla, revisar **Deploys → Logs** y corregir el PR; no ejecutar migraciones manuales sobre producción sin una copia de seguridad.
5. Anotar la URL HTTPS `https://bigmedia-web.onrender.com` que Render asigne. Si el nombre final cambia, usar el valor real del panel.

## Verificar antes de ingresar datos

1. Abrir la URL raíz: debe cargar React por HTTPS. `/static/assets/` debe responder CSS y JavaScript; `/api/health/` debe devolver `{"status":"ok"}`. Un 503 indica que la API no puede conectar con PostgreSQL.
2. En **Shell** del servicio web ejecutar `python manage.py check --deploy`. Las advertencias `security.W005` y `security.W021` son deliberadas mientras se use el subdominio `onrender.com`: Big Media no controla todos sus subdominios y por eso no habilitamos HSTS para subdominios ni preload. Investigar cualquier otra advertencia.
3. Ejecutar `python manage.py showmigrations` en Shell y comprobar que las migraciones están aplicadas. Repetir tras un nuevo despliegue para confirmar que la base persiste.
4. Crear el primer administrador con `python manage.py createsuperuser` desde Shell. Usar una contraseña única; no guardarla en el repositorio. Ingresar a `/admin/` y confirmar que un usuario no autenticado no puede administrar datos.
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
