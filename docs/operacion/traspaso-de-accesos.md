# Traspaso de accesos

Lista de verificación para que el código, la base y los accesos queden a nombre de Big Media
(HU-053, criterio 3). Completar el traspaso es una tarea de personas: este documento la guía y deja
registro de cuándo se hizo cada paso y quién lo verificó.

> **Este documento nunca lleva credenciales** (regla 2 de [`CLAUDE.md`](../../CLAUDE.md)): ni
> contraseñas, ni URLs de base con usuario y clave, ni tokens. Las contraseñas se pasan en persona o
> con un gestor de contraseñas, nunca por chat ni correo, y se cambian después del traspaso.

## Antes de empezar

- [ ] Big Media eligió quién va a ser el **dueño de las cuentas** (una persona con correo de la
      empresa, no un correo personal) y quién queda como **segundo administrador**, para no
      depender de una sola persona.
- [ ] Big Media tiene un **gestor de contraseñas** propio (por ejemplo Bitwarden o 1Password) donde
      van a quedar todas las claves de esta lista.
- [ ] Se fijó una fecha para el traspaso, con alguien del equipo de desarrollo presente.

## Accesos

Por cada acceso: quién lo tiene hoy, a quién pasa, cómo se transfiere y cómo se comprueba que quedó
bien. La columna **Hecho** se completa con la fecha y las iniciales de quien lo verificó.

| # | Acceso | Hoy | Pasa a | Cómo se transfiere | Cómo se verifica | Hecho |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Repositorio GitHub `jdcaballero15/BigMedia` | Cuenta personal de Juan Diego | Organización de GitHub de Big Media | Big Media crea una organización gratis. Juan Diego va a **Settings → Transfer ownership** y la elige. GitHub redirige la URL vieja | El repositorio aparece en la organización; el dueño de Big Media es **Owner**; la protección de `main` y `develop` sigue activa (**Settings → Branches**) | |
| 2 | Render: workspace con `bigmedia-web`, `bigmedia-db` y `bigmedia-web-staging` | A completar | Workspace de Render de Big Media | Invitar al dueño de Big Media como **Owner** del workspace (o transferir los servicios a su workspace). Reconectar el Blueprint al repositorio en su nueva ubicación | El dueño de Big Media entra y ve los tres servicios; un deploy de `develop` actualiza staging; `/api/health/` responde `{"status":"ok"}` en los dos entornos | |
| 3 | Facturación de Render | A completar | Tarjeta o medio de pago de Big Media | Lo carga Big Media en **Billing** del workspace | La próxima factura sale a nombre de Big Media | |
| 4 | Neon: proyecto `bigmedia-staging` | A completar | Cuenta u organización de Neon de Big Media | Transferir el proyecto (**Settings → Transfer project**) o invitar al dueño de Big Media | El dueño de Big Media ve el proyecto; staging sigue respondiendo | |
| 5 | Superusuario de Django en producción | Quien lo creó en el primer deploy | Administrador de Big Media | El administrador de Big Media crea su propio usuario con rol Administrador desde **Administración › Usuarios** | Entra con su usuario y ve **Usuarios** y **Parámetros** | |
| 6 | Superusuario de Django en staging | Quien lo creó en el primer deploy | Administrador de Big Media | Igual que el anterior, en staging | Igual que el anterior | |
| 7 | Dominio propio, si se usa | A completar (o "no aplica") | Big Media | Transferir el dominio a una cuenta de Big Media y apuntarlo a Render (**Settings → Custom Domains**) | La URL del dominio carga la aplicación por HTTPS | |
| 8 | Correo para avisos a Administración (HU-067), si se configura | A completar (o "no aplica") | Big Media | Cuenta de correo o de proveedor de envío a nombre de Big Media. En **Environment** de cada servicio de Render se cargan `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL` y `FACTURACION_CORREO_ADMINISTRACION` | Reabrir un ítem Enviado de prueba en staging hace llegar el aviso a la dirección de Administración | |
| 9 | Planillas e historias originales fuera de Git | Equipo de desarrollo | Carpeta compartida de Big Media | Copiar los archivos a la carpeta de Big Media | Big Media los abre desde su carpeta | |

## Después del traspaso: rotar todo

Cualquier clave que conoció el equipo de desarrollo se cambia. Cada valor nuevo va solo al gestor de
contraseñas de Big Media y al panel donde se usa.

- [ ] **`DJANGO_SECRET_KEY`** de producción y de staging: generar un valor nuevo en
      **Environment** de cada servicio de Render y redeplegar. Cierra todas las sesiones abiertas.
- [ ] **Contraseña de la base de producción** (`bigmedia-db`): rotarla en Render. La `DATABASE_URL`
      de `bigmedia-web` se toma de la base, así que se actualiza sola; comprobar `/api/health/`.
- [ ] **Contraseña de la base de staging** en Neon: rotarla y pegar la `DATABASE_URL` nueva en
      `bigmedia-web-staging`. Comprobar `/api/health/`.
- [ ] **`DJANGO_SUPERUSER_PASSWORD`** de los dos entornos: cambiar la contraseña del superusuario
      desde la aplicación y borrar o reemplazar la variable en Render (`asegurar_admin` no pisa una
      contraseña existente).
- [ ] **`DJANGO_DEMO_PASSWORD`** de staging: cambiarla o dejarla vacía.
- [ ] **`EMAIL_HOST_PASSWORD`** de los dos entornos, si el correo de avisos está configurado:
      generar una clave nueva en el proveedor de correo y reemplazarla en Render.
- [ ] **Usuarios del equipo de desarrollo** en la aplicación: inactivarlos desde **Administración ›
      Usuarios**, salvo que Big Media quiera mantener a alguien para soporte.
- [ ] **Colaboradores de GitHub, Render y Neon**: quitar al equipo de desarrollo o bajarlo a un
      permiso de lectura, según lo que decida Big Media.

## Cierre

- [ ] Big Media levantó una copia local siguiendo [desarrollo local](desarrollo-local.md), o lo
      hizo alguien de su confianza ajeno al equipo original.
- [ ] Big Media tiene la [guía de contribución](../guia-de-contribucion.md) y el
      [despliegue en Render](despliegue-render.md) para su próximo equipo.
- [ ] Se hizo una prueba de recuperación de la base según
      [Recuperación y copias](despliegue-render.md#recuperación-y-copias).

| Fecha del traspaso | Por Big Media | Por el equipo de desarrollo |
| --- | --- | --- |
| | | |
