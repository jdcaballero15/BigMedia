# ADR-0011 — Guardar las órdenes de publicidad en Cloudflare R2

- **Estado:** Propuesto
- **Fecha:** 2026-11-07
- **Decidido por:** Juan Diego
- **Módulos afectados:** campanias, infra

---

## Contexto

HU-069 pide adjuntar a la campaña la orden de publicidad que manda el cliente. Es un PDF de
varias páginas (hasta 10) y una campaña puede tener más de uno. Muchas llegan escaneadas, así que
cada archivo puede pesar varios MB, bastante más que la orden de compra de HU-062.

Hoy el único archivo que suben los usuarios es el PDF de la orden de compra, y se guarda en
PostgreSQL ([ADR-0009](0009-pdf-de-orden-de-compra-en-postgresql.md)). Ese ADR descartó un bucket
porque sumaba una dependencia, credenciales y una cuenta más para el traspaso, y dejó anotado que,
si se suben muchos archivos o muy grandes, habría que pasar a un almacenamiento de objetos. Con
las órdenes de publicidad llega el segundo tipo de archivo, más pesado y con varios por campaña.
El disco de la web en Render se sigue borrando en cada deploy.

## Decisión

> Vamos a guardar las órdenes de publicidad en un bucket privado de Cloudflare R2, con
> `django-storages` y `boto3`.

- Hay un bucket por entorno (producción y staging), los dos privados y sin dominio público.
- El acceso usa la API compatible con S3 de R2 y el backend `S3Storage` de `django-storages`.
  Las credenciales salen de un token de R2 limitado a lectura y escritura de objetos en ese
  bucket, y van por variables de entorno: `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`,
  `R2_SECRET_ACCESS_KEY` y `R2_BUCKET`.
- La clave del objeto no usa el nombre original del archivo, que puede traer datos del cliente:
  es `campanias/<id de campaña>/ordenes-publicidad/<uuid>.pdf`. El nombre original, el tamaño,
  quién lo subió y cuándo quedan en la base.
- Para abrir una orden, la API verifica la sesión y el permiso y devuelve una URL firmada que
  vence a los pocos minutos. El archivo no pasa por Django.
- Se acepta solo PDF: extensión `.pdf` y contenido que empieza con `%PDF-`. El tamaño máximo es
  de 10 MB, configurable con `CAMPANIAS_OP_MAX_MB`.
- Dar de baja una orden la marca inactiva en la base y no borra el objeto del bucket (HU-006).
- Sin `R2_BUCKET` (desarrollo local) se usa `FileSystemStorage` en una carpeta ignorada por git.
  Los tests usan `InMemoryStorage` y no tocan la red.
- La orden de compra de HU-062 sigue en PostgreSQL. Pasarla a R2 es otra decisión, con su propio
  ADR.

## Alternativas consideradas

| Alternativa | Ventajas | Por qué se descartó |
| --- | --- | --- |
| PostgreSQL, como la orden de compra (ADR-0009) | Sin cuentas ni dependencias nuevas; entra en los backups de la base | Archivos más pesados y varios por campaña hacen crecer la base y sus backups; Juan Diego prefirió separar los archivos de los datos ahora |
| AWS S3 | Es el estándar y `django-storages` lo soporta igual | Cobra la descarga de archivos y la cuenta de AWS es más difícil de traspasar y de acotar |
| Disco persistente de Render | `FileField` sin dependencias | Es pago, ata la web a una sola instancia y no existe en staging (mismo motivo que en ADR-0009) |

## Consecuencias

**Positivas**
- La base no crece con los PDF y los backups siguen siendo livianos.
- Abrir una orden no carga la web de Render: el navegador la baja directo de R2.
- R2 no cobra la descarga y el plan gratis alcanza holgado para este volumen.
- Si más adelante hay otros archivos (por ejemplo, fotos de carteles), se suman con el mismo
  mecanismo.

**Negativas / costo que aceptamos**
- Una cuenta más en el traspaso (Cloudflare), con su token, que hay que documentar en la entrega.
- Dos dependencias nuevas en el backend: `django-storages` y `boto3`.
- Los backups de la base no incluyen los archivos. Hay que activar el versionado o una copia del
  bucket aparte si se quiere poder recuperarlos.
- Si se sube el archivo y falla el guardado en la base, queda un objeto huérfano en el bucket.
  Primero se sube y después se guarda la fila; los huérfanos se pueden limpiar más adelante.

**Qué se vuelve más difícil**
- Probar en local el camino real a R2: los tests usan almacenamiento en memoria, así que la
  configuración del bucket se comprueba en staging.
- Conviven dos formas de guardar archivos (PostgreSQL para la orden de compra y R2 para la orden
  de publicidad) hasta que se decida unificarlas.

## Impacto en las reglas del repositorio

Se aplica en el PR de la unidad que implementa HU-069.

- [ ] `CLAUDE.md`
- [ ] `docs/estandares-de-codigo.md`
- [x] `pyproject.toml`, `requirements-dev.txt` o la configuración del frontend
- [ ] `.github/workflows/ci.yml`
- [x] `backend/.env.example`

También `render.yaml` (variables `R2_*` en producción, sin valores) y la documentación de traspaso
(cuenta de Cloudflare y token).

## Referencias

- HU-069 en [`historias-de-usuario.md`](../aidlc/inputs/historias-de-usuario.md).
- [ADR-0009](0009-pdf-de-orden-de-compra-en-postgresql.md): orden de compra en PostgreSQL.
- [ADR-0005](0005-base-de-staging-en-neon.md): entornos de producción y staging.
