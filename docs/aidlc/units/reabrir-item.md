# Unidad: Reabrir un ítem enviado

- **Estado:** en revisión · **Épica:** E11 Facturación mensual · **App dueña:** `facturacion`
- **Origen:** HU-067 (RN-022) · **Rama:** `feature/facturacion-reabrir-item`

## Objetivo

Un ítem Enviado a facturar se puede reabrir con motivo para corregirlo, dejando registro, y
Administración recibe un aviso por correo con lo que cambió. Al volver a enviarlo, regresa a
Enviado y queda marcado como reenviado.

## Decisiones

1. **Sin reabrir no se edita** (criterio 1): ya funciona desde HU-065. Se agrega el test.
2. **Reabrir** (criterio 2): `POST /api/facturacion/items/<id>/reabrir/` con `{motivo}`
   obligatorio. El ítem vuelve a Borrador con `reabierto_en`, `reabierto_por` y `motivo_reapertura`,
   y el cambio queda en la auditoría. Solo se reabre un Enviado; un Facturado no (HU-067 lo deja
   por definir).
3. **Aviso a Administración** (criterio 3, RN-022 provisoria): dos correos, para no mandar uno por
   cada guardado.
   - Al reabrir: qué ítem, quién, motivo, y que no se facture hasta el reenvío.
   - Al reenviar: los valores anteriores y nuevos de cada campo que cambió desde la reapertura.
   Se envían con `transaction.on_commit`, así un error de la transacción no manda correo. Si el
   correo falla, se registra en el log y la operación sigue.
4. **Reenviar** (criterio 4): el ítem reabierto vuelve a salir con "Enviar a facturar" del mes,
   como cualquier Borrador. Al enviarse queda con `reenviado = True`, y la planilla lo marca.
5. **Correo con Django, sin dependencias nuevas**: backend SMTP configurado por variables de
   entorno. En desarrollo y tests, backend de consola o de memoria. Si no hay dirección de
   Administración configurada, no se envía y queda en el log.

## Cambios

- `facturacion/models.py`: `reabierto_en`, `reabierto_por`, `motivo_reapertura`, `reenviado`.
- `facturacion/services.py`: `reabrir(item, motivo, usuario)`, el marcado de reenviado en
  `enviar_a_facturar` y `avisar_a_administracion(...)`.
- `facturacion/views.py` y `urls.py`: la acción `reabrir`.
- `config/settings.py` y `backend/.env.example`: `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`,
  `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL` y
  `FACTURACION_CORREO_ADMINISTRACION`.
- `render.yaml` (las variables, sin valores) y `docs/operacion/traspaso-de-accesos.md` (la
  cuenta de correo de envío).
- Frontend: botón "Reabrir" con motivo en los ítems Enviados, y la marca "Reenviado" en el
  listado.

## Migraciones

Una en `facturacion`: cuatro campos opcionales en el ítem. No mueve datos.

## Reglas provisorias que se usan

- RN-022: Administración recibe los avisos por correo.

## Cómo se prueba

- `backend/tests/test_reabrir_item.py` (correo con `mail.outbox`):
  - Un Enviado no se edita sin reabrir (criterio 1).
  - Reabrir pide motivo y registra quién, cuándo y por qué (criterio 2).
  - Reabrir y reenviar mandan los avisos, el segundo con valores anteriores y nuevos
    (criterio 3, `@pytest.mark.regla("RN-022")`).
  - El reenvío vuelve a Enviado y queda marcado (criterio 4).
  - No se reabre un Borrador, un Facturado ni un Anulado. Lectura recibe 403.
  - Sin dirección configurada no se manda correo y el reabrir funciona igual.
- Frontend: `ItemsPage.test.tsx` (reabrir con motivo y marca de reenviado).

## Registro de gates

- Gate 1 (plan): 2026-10-27 — aprobado por Gonza
- Gate 2 (verificación): 2026-10-27 — `ruff format --check` (135 archivos) y `ruff check` sin
  errores; `mypy backend` sin errores (135 archivos); `makemigrations --check` sin cambios;
  `pytest --cov`: 767 tests en verde, coverage 96,89 %; frontend `format:check`, `lint`,
  `typecheck` y `build` en verde, `test:coverage` con 327 tests en verde y 93,64 % de líneas
  (91,18 % de sentencias); `pre-commit run --all-files` en verde. Aprobado por Gonza el
  2026-10-27, con dos ajustes al plan: un quinto campo, `valores_al_reabrir` (el ítem como sale
  en la planilla al reabrirlo), y el aviso de reenvío compara las columnas de la planilla.
- Gate 3 (PR): pedido por Gonza el 2026-10-27
