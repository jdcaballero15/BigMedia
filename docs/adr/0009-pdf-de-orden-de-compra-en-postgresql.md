# ADR-0009 — Guardar el PDF de la orden de compra en PostgreSQL

- **Estado:** Propuesto
- **Fecha:** 2026-10-27
- **Decidido por:** Gonza
- **Módulos afectados:** facturacion, infra

---

## Contexto

HU-062 pide adjuntar al ítem a facturar el PDF de su orden de compra y poder abrirlo desde el
ítem. Es el primer archivo que suben los usuarios. En Render el disco de la web se borra en cada
deploy, y el sistema no tiene almacenamiento de archivos: producción usa la base de Render y
staging la de Neon ([ADR-0005](0005-base-de-staging-en-neon.md)). Son pocos archivos por mes,
de unos cientos de KB, y el traspaso tiene que sumar la menor cantidad posible de cuentas.

## Decisión

> Vamos a guardar el PDF de la orden de compra como binario en PostgreSQL.

- El modelo `facturacion.OrdenCompraPdf` guarda el contenido (`BinaryField`), el nombre, el tamaño,
  quién lo subió y cuándo. Hay uno por ítem, y subir otro lo reemplaza.
- Va en un modelo aparte del ítem, así listar ítems no trae el contenido.
- Se acepta solo PDF: la extensión `.pdf` y un contenido que empiece con `%PDF-`.
- El tamaño máximo es de 5 MB, configurable con `FACTURACION_OC_MAX_MB`.
- `GET /api/facturacion/items/<id>/orden-compra-pdf/` lo devuelve para abrirlo en el navegador.

## Alternativas consideradas

| Alternativa | Ventajas | Por qué se descartó |
| --- | --- | --- |
| Disco persistente de Render | `FileField` de Django sin cambios | Es pago, ata la web a una sola instancia y no existe en staging |
| Bucket S3 o Cloudflare R2 con `django-storages` | Escala a muchos archivos grandes | Suma una dependencia, credenciales y una cuenta más para el traspaso |
| Guardar solo número y fecha, sin PDF | Nada nuevo | HU-062 pide el PDF como respaldo de lo que se factura |

## Consecuencias

**Positivas**
- El PDF entra en los backups de la base y en el mismo traspaso, sin cuentas nuevas.
- Funciona igual en desarrollo, staging y producción.
- Se borra o se protege junto con el ítem, con las mismas reglas (`PROTECT`).

**Negativas / costo que aceptamos**
- La base crece con los PDF. Con el tope de 5 MB y pocos ítems por mes, es poco frente al plan
  de la base.
- Servir el archivo pasa por Django y no por un CDN. Para abrir una OC por vez, alcanza.

**Qué se vuelve más difícil**
- Si algún día se suben muchos archivos o muy grandes, habrá que migrarlos a un almacenamiento de
  objetos. El acceso está concentrado en `OrdenCompraPdf` y en una sola vista, así que el cambio
  queda acotado.

## Impacto en las reglas del repositorio

- [ ] `CLAUDE.md`
- [ ] `docs/estandares-de-codigo.md`
- [ ] `pyproject.toml`, `requirements-dev.txt` o la configuración del frontend
- [ ] `.github/workflows/ci.yml`
- [x] `backend/.env.example`

## Referencias

- HU-062 en [`historias-de-usuario.md`](../aidlc/inputs/historias-de-usuario.md).
- Unidad [orden-de-compra-y-grupos](../aidlc/units/orden-de-compra-y-grupos.md).
