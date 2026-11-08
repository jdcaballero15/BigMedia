# Unidad: Orden de publicidad de la campaña

- **Estado:** en curso · **Épica:** E4 Campañas · **App dueña:** `campanias`
- **Origen:** HU-069, [ADR-0011](../../adr/0011-orden-de-publicidad-en-cloudflare-r2.md) · **Rama:** `feature/campanias-orden-de-publicidad`

## Objetivo

En el formulario de Nueva campaña (y al editarla) se pueden adjuntar uno o más PDF de la orden de
publicidad que manda el cliente. Quedan guardados en Cloudflare R2 y después se abren desde la
campaña. Es la primera unidad que usa almacenamiento de objetos.

## Decisiones

1. **Un solo guardado para la campaña y sus PDF** (HU-069, criterio 4): el formulario manda la
   campaña y los PDF en el mismo pedido (`multipart/form-data`) solo cuando hay archivos; sin
   archivos sigue mandando JSON como hoy. El servidor valida los PDF antes de tocar la base y crea
   o edita la campaña, sube los archivos y guarda las filas dentro de una transacción. Si un PDF
   se rechaza, no se guarda nada y el formulario conserva lo cargado.
   - Alternativa descartada: guardar la campaña y subir el PDF en un segundo pedido. Es más
     simple, pero si el PDF falla queda la campaña creada sin su orden, que es justo lo que el
     criterio 4 no quiere.
2. **Modelo `OrdenPublicidad`** en `campanias`: campaña (`PROTECT`), archivo (`FileField`), nombre
   original, tamaño, subida por, subida en, `activa`, dada de baja por y en. Varias por campaña.
3. **Clave del objeto**: `campanias/<id de campaña>/ordenes-publicidad/<uuid>.pdf`. El nombre
   original queda solo en la base (ADR-0011).
4. **Validación**: la misma que la orden de compra (extensión `.pdf` y contenido que empieza con
   `%PDF-`), con tope de `CAMPANIAS_OP_MAX_MB` (default 10). La función `validar_pdf` de
   `facturacion` no se importa (`campanias` no puede importar de `facturacion`): se escribe una
   propia en `campanias/services.py`.
5. **Abrir una orden**: `GET /api/campanias/ordenes-publicidad/<id>/archivo/` verifica sesión y
   permiso. Con R2 responde una redirección a una URL firmada que vence en 5 minutos (el archivo
   no pasa por Django). Sin R2 (desarrollo local) devuelve el archivo desde el disco.
6. **Dar de baja**: `POST /api/campanias/ordenes-publicidad/<id>/dar-de-baja/` marca `activa =
   False`, guarda quién y cuándo, y no borra el objeto del bucket (HU-006). Las dadas de baja
   siguen en el histórico de la campaña (criterio 5).
7. **Permisos**: los de la campaña (`LecturaConSesionEdicionOperativo`): Operativo y
   Administrador adjuntan y dan de baja, Lectura abre (criterio 6), sin sesión se niega
   (criterio 7).
8. **Auditoría**: adjuntar y dar de baja quedan registrados en la auditoría de la campaña, con
   `registrar_cambios` (campo `ordenes_publicidad`, con el nombre del archivo).
9. **Almacenamiento por entorno**:
   - Con `R2_BUCKET` definido: `storages.backends.s3.S3Storage` apuntando a
     `https://<R2_ACCOUNT_ID>.r2.cloudflarestorage.com`, bucket privado, URLs firmadas.
   - Sin `R2_BUCKET` (desarrollo local): `FileSystemStorage` en `backend/media/`, ignorada por git.
   - Tests: `InMemoryStorage`, sin red.
   - Los estáticos siguen con WhiteNoise, sin cambios.

## Cambios

- `backend/pyproject.toml`: `django-storages[s3]` (trae `boto3`). El código no importa `storages`
  ni `boto3`: se configuran por nombre en `STORAGES`, así que mypy no necesita stubs nuevos.
- `config/settings.py`: `STORAGES["default"]` según `R2_BUCKET`, `MEDIA_ROOT`, `MEDIA_URL`, las
  variables `R2_*` y `CAMPANIAS_OP_MAX_MB`.
- `backend/.env.example`: `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`,
  `R2_BUCKET` (vacías) y `CAMPANIAS_OP_MAX_MB=10`.
- `render.yaml`: las variables `R2_*` en producción y en staging, con `sync: false` (sin valores).
- `.gitignore`: `backend/media/`.
- `campanias/models.py`: `OrdenPublicidad`.
- `campanias/services.py`:
  - `validar_pdf_orden_publicidad(archivo)`.
  - `adjuntar_ordenes_publicidad(campania, archivos, usuario)`.
  - `dar_de_baja_orden_publicidad(orden, usuario)`.
- `campanias/serializers.py`: la campaña expone `ordenes_publicidad` (id, nombre, tamaño, subida
  por, subida en, activa) de solo lectura.
- `campanias/views.py` y `urls.py`:
  - `CampaniaViewSet` acepta multipart en `create` y `partial_update`, con los archivos en el campo
    `ordenes_publicidad`.
  - `OrdenPublicidadViewSet` (solo lectura) con las acciones `archivo` y `dar-de-baja`.
- Frontend (`features/campanias`):
  - `CampaniaForm`: campo para adjuntar uno o más PDF, con su lista antes de guardar y la opción
    de sacar uno de la lista. Si hay archivos, guarda con `apiUpload`; si no, como hoy.
  - `CampaniaDetalle`: sección "Órdenes de publicidad" con nombre, quién la subió y cuándo, un
    enlace para abrirla y "Dar de baja" (no para Lectura). Las dadas de baja aparecen aparte,
    como histórico.
  - `types.ts`: el tipo `OrdenPublicidad`.
- `docs/manual/manual-de-uso.md`: cómo adjuntar y abrir la orden de publicidad.
- `docs/operacion/traspaso-de-accesos.md`: cuenta de Cloudflare, buckets y token de R2.
- `docs/operacion/despliegue-render.md`: variables `R2_*` en cada entorno.
- `docs/modelo-de-datos.md`: `OrdenPublicidad`.

## Migraciones

Una nueva en `campanias`: crea `OrdenPublicidad`. No mueve datos.

## Reglas provisorias que se usan

Ninguna.

## Cómo se prueba

- Backend (`backend/tests/test_orden_publicidad.py`, con `InMemoryStorage`):
  - `test_crear_campania_con_pdf_guarda_la_orden` (criterio 1).
  - `test_campania_expone_sus_ordenes_con_nombre_usuario_y_fecha` (criterio 2).
  - `test_editar_campania_con_otro_pdf_conserva_las_dos` (criterio 3).
  - `test_crear_campania_con_archivo_no_pdf_no_guarda_nada` y
    `test_crear_campania_con_pdf_mayor_al_maximo_no_guarda_nada` (criterio 4).
  - `test_dar_de_baja_orden_la_saca_de_vigentes_y_no_borra_el_archivo` (criterio 5).
  - `test_lectura_abre_la_orden_pero_no_adjunta_ni_da_de_baja` (criterio 6).
  - `test_archivo_sin_sesion_se_niega` (criterio 7).
  - `test_crear_y_confirmar_campania_sin_orden_se_acepta` (criterio 8).
  - `test_clave_del_objeto_no_usa_el_nombre_original` y
    `test_adjuntar_y_dar_de_baja_quedan_auditados`.
  - `test_archivo_con_r2_redirige_a_url_firmada` (con el storage simulado, sin red).
- Frontend: `CampaniaForm.test.tsx` (adjuntar, sacar de la lista, guardar con multipart y
  conservar lo cargado ante un error) y `CampaniaDetalle.test.tsx` (lista, abrir, dar de baja y
  sin acciones para Lectura).
- Prueba manual en staging, con el bucket real: crear una campaña con un PDF de 10 páginas,
  abrirlo y darlo de baja.

## Fuera de alcance

- Pasar la orden de compra de HU-062 a R2 (sigue en PostgreSQL, ADR-0009).
- Limpiar objetos huérfanos del bucket.
- Versionado o copia de seguridad del bucket (se configura en Cloudflare, no en el código).

## Antes de la prueba en staging (lo hace Juan Diego)

- Crear los buckets privados `bigmedia-prod` y `bigmedia-staging` en Cloudflare R2.
- Crear un token de R2 con lectura y escritura de objetos limitado a esos buckets.
- Cargar las variables `R2_*` en Render (producción y staging).

## Registro de gates

- Gate 1 (plan): 2026-11-07 — aprobado por Juan Diego
- Gate 2 (verificación): 2026-11-07 — aprobado por Juan Diego el 2026-11-08. Salida de los comandos:
  - `ruff format --check .`: `147 files left unchanged`. `ruff check .`: `All checks passed!`
  - `mypy backend`: `Success: no issues found in 147 source files`
  - `makemigrations --check --dry-run`: `No changes detected` (la `0006_orden_publicidad`, revisada
    a mano, solo crea la tabla)
  - `pytest --cov`: `936 passed in 2499.53s`, ninguno salteado; `Total coverage: 97.32%`. Las
    líneas de `campanias` quedan cubiertas; en `settings.py` queda sin cubrir la rama con
    `R2_BUCKET` (línea 116), que se prueba en staging.
  - Frontend: `format:check` (`All matched files use Prettier code style!`), `lint` y `typecheck`
    sin errores, `test:coverage` con `405 passed` (sentencias 92,85 %, líneas 94,83 %), `build`
    `✓ built in 1m 2s` (con el aviso de chunk de más de 500 kB, que ya existía).
  - `pre-commit run --all-files`: todos `Passed`, incluido gitleaks (`Detect hardcoded secrets`).
  - Falta la prueba manual en staging con el bucket real.
- Gate 3 (PR): pendiente
