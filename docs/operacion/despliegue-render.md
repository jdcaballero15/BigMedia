# Despliegue de Big Media en Render

Big Media corre en dos entornos ([ADR-0005](../adr/0005-base-de-staging-en-neon.md)). `render.yaml`
los describe, pero su presencia en Git no crea recursos: se crean al aplicar el Blueprint desde el
panel de Render.

## Entornos

| Entorno | Rama | Web | Base | Para qué |
| --- | --- | --- | --- | --- |
| **Producción** | `main` | `bigmedia-web`, Render Starter (pago) | `bigmedia-db`, Render Basic-256mb (pago) | Datos reales, con copias de seguridad |
| **Staging** | `develop` | `bigmedia-web-staging`, Render gratis | Proyecto `bigmedia-staging` en **Neon** gratis | Probar lo nuevo antes de producción y hacer demos |

- **Producción** (`DJANGO_ENV=production`): la web se conecta a la base por la red interna de Render.
  Costo aproximado: ~USD 7/mes la web y ~USD 6/mes la base más disco (confirmar en el panel).
- **Staging** (`DJANGO_ENV=staging`): seguridad igual que producción (HTTPS, `DEBUG` off) y **arranca
  con datos de ejemplo** que crea `python manage.py cargar_datos_ejemplo` (idempotente; nunca datos
  reales; se niega a correr en producción). La base de Neon gratis no vence; si se recrea, el arranque
  vuelve a migrar y cargar los datos de ejemplo.
- **Datos para demos en staging:** además del primer lote, el comando carga un lote demo
  (`_datos_demo.py`) que llena todas las pantallas: 20 carteles en los 7 formatos, proveedores,
  rubros, 8 clientes, 13 marcas, campañas y reservas en todos los estados (de 5 meses atrás a 3
  adelante), costos y auditoría. Las fechas se calculan el día que corre; para refrescarlas hay que
  recrear la base. Si `DJANGO_DEMO_PASSWORD` está cargada, crea `demo-operativo`, `demo-gerencia` y
  `demo-lectura` (uno por rol de HU-004) con esa contraseña.

Flujo: un cambio entra a `develop` → Render actualiza staging → se prueba → release a `main` →
Render actualiza producción.

## Límites del plan gratis (staging)

- **La web se duerme** después de 15 minutos sin tráfico. La primera visita tarda cerca de un minuto.
- **La base de Neon se suspende** tras unos minutos sin consultas; la primera consulta después tarda
  algo más.
- Neon gratis tiene espacio y horas de cómputo limitados por mes (alcanza para staging). Ver
  [neon.com/pricing](https://neon.com/pricing).
- No hay Shell en la web gratis: la imagen migra la base y crea el primer administrador en cada
  arranque (`backend/arrancar.sh`).

## Crear la base de staging en Neon

1. Crear una cuenta en [neon.com](https://neon.com) y un proyecto `bigmedia-staging`, con
   **Postgres 17** y región **AWS us-east-1 (N. Virginia)**, la misma que Render.
2. En **Connect**, desactivar **Connection pooling** y copiar la connection string **directa** (el
   host no dice `-pooler`). Debe terminar con `?sslmode=require`.
3. Esa URL tiene la contraseña: se pega solo en el panel de Render (paso 4 de la sección siguiente).
   No va a Git, ni a chats, ni a documentos.

## Crear o actualizar los servicios

Orden recomendado:

1. **Producción a pago.** En el panel de Render, cambiar `bigmedia-db` a **Basic-256mb** y
   `bigmedia-web` a **Starter**, y revisar el precio antes de confirmar. Hacerlo antes de que venza la
   base gratis (17/11/2026). `render.yaml` ya declara esos planes, así que una sincronización del
   Blueprint no los vuelve a gratis.
2. **Release.** `main` tiene que tener el CI en verde: Render solo despliega commits de `main` cuyos
   checks pasaron (`autoDeployTrigger: checksPass`).
3. **Blueprint.** En Render, **Blueprints** → el Blueprint de `jdcaballero15/BigMedia` → **Sync** (o
   **New Blueprint Instance** si todavía no existe, rama `main`).
4. Render pide los valores que no están en Git:
   - `DATABASE_URL` de `bigmedia-web-staging`: la URL directa de Neon.
   - `DJANGO_SUPERUSER_USERNAME` y `DJANGO_SUPERUSER_PASSWORD`, para cada entorno (pueden ser
     distintos). Contraseñas largas y únicas; no las guardes en el repositorio ni las mandes por chat.
   - `DJANGO_DEMO_PASSWORD`, solo en staging y opcional: la contraseña de los usuarios de demo. Tiene
     que estar cargada antes del primer arranque con el lote demo, porque los usuarios se crean junto
     con ese lote.
5. Esperar el build. En **Logs** tienen que aparecer las migraciones, `Administrador <usuario> creado.`
   y `Listening at`. El chequeo `/api/health/` debe dar `{"status":"ok"}`. En staging, además, la carga
   de datos de ejemplo.
6. Anotar las URLs que asigna Render (por ejemplo `https://bigmedia-web.onrender.com`).

La `DATABASE_URL` de producción viene de la URL interna de `bigmedia-db` y `DJANGO_SECRET_KEY` la
genera Render. Nunca copiar esos valores a Git ni a mensajes. Si se rota la contraseña en Neon, hay
que actualizar la `DATABASE_URL` de staging en el panel de Render.

El comando `asegurar_admin` no hace nada si el usuario ya existe, así que cambiar la contraseña desde
`/admin/` es seguro: un nuevo deploy no la pisa.

## Ver tablas y esquema

El esquema lo definen los modelos de Django y lo crean las migraciones. **Nunca se cambia a mano** en
ninguna base: todo cambio va por una migración en un PR.

- **Local:** la forma más segura de explorar el esquema (es idéntico al de los entornos). Conectar un
  cliente SQL (por ejemplo DBeaver) a la base de Docker Compose con los datos de `backend/.env`.
- **Staging (Neon):** el panel de Neon tiene **Tables** (visor de tablas) y **SQL Editor**.
- **Producción (Render):** Render no tiene visor de tablas.
  - Para ver o editar registros: el admin de Django (`/admin/`).
  - Para consultas SQL puntuales: agregar la IP propia en **bigmedia-db → Access Control** (hoy
    `ipAllowList: []` no deja entrar desde afuera), conectar un cliente SQL con la **External Database
    URL**, usar un usuario de solo lectura y sacar la IP al terminar.

## Primeros pasos en producción

1. Abrir la URL: debe cargar la app por HTTPS. `/api/health/` debe responder `{"status":"ok"}`.
2. Entrar a `/admin/` con el administrador. Crear una cuenta por persona (Seba, socios), sin cuentas
   compartidas, y asignar el grupo **Operativo** a quien vaya a cargar o editar carteles.
3. Probar con esas cuentas: inicio y cierre de sesión, lectura de carteles, edición con permiso y
   rechazo de edición sin permiso.

## Pasar al plan pago

Solo producción. Hacerlo antes de que venza la base gratis (17/11/2026) y siempre antes de cargar el
inventario real.

1. En el panel de Render, cambiar `bigmedia-db` a `basic-256mb` y `bigmedia-web` a `starter`, los
   planes que declara `render.yaml`. Revisar el precio en el panel antes de confirmar.
2. Con la web paga se puede agregar `preDeployCommand: python manage.py migrate --noinput` en un PR
   aparte. El arranque de la imagen sigue migrando y no molesta: si no hay migraciones pendientes, no
   hace nada.
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
- Mantener datos reales fuera de bases de desarrollo y pruebas locales. El entorno local usa `backend/.env` y Docker Compose según [desarrollo local](desarrollo-local.md).
