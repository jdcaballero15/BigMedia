# ADR-0008 — Generar la planilla de facturación en el servidor con `openpyxl`

- **Estado:** Propuesto
- **Fecha:** 2026-10-27
- **Decidido por:** Gonza
- **Módulos afectados:** facturacion, infra

---

## Contexto

HU-066 pide que "Enviar a facturar" genere una planilla .xlsx para Administración con los ítems
enviados. Cada envío queda registrado (quién, cuándo y qué ítems), y la planilla tiene que
coincidir con ese registro y poder volver a descargarse. El repositorio no tenía ninguna librería
para escribir .xlsx: los reportes de E8 se exportan a CSV y PDF desde el navegador.

## Decisión

> Vamos a generar la planilla en el backend con `openpyxl` (`>=3.1,<4`).

`apps/facturacion/services.py::planilla_xlsx` arma el archivo a partir del envío guardado, y
`GET /api/facturacion/envios/<id>/planilla/` lo descarga. Para `mypy --strict` se suma
`types-openpyxl` a `requirements-dev.txt`, con versión fija.

## Alternativas consideradas

| Alternativa | Ventajas | Por qué se descartó |
| --- | --- | --- |
| Generar el .xlsx en el navegador (SheetJS u otra) | No suma dependencias al backend | Suma una librería pesada al frontend, y la planilla queda desacoplada del envío registrado |
| Exportar CSV, como los reportes | Sin dependencias nuevas | HU-066 pide .xlsx, y el CSV pierde los tipos de las columnas (importes como texto) |

## Consecuencias

**Positivas**
- La planilla sale del mismo registro que el envío, así que no puede contradecirlo.
- Los importes se escriben como números, que Administración puede sumar.
- Se prueba en `pytest` leyendo el archivo generado.

**Negativas / costo que aceptamos**
- El backend suma una dependencia de ejecución y otra de tipos.

**Qué se vuelve más difícil**
- Nada relevante: `openpyxl` es puro Python y no necesita nada del sistema operativo en la imagen.

## Impacto en las reglas del repositorio

- [ ] `CLAUDE.md`
- [ ] `docs/estandares-de-codigo.md`
- [x] `pyproject.toml`, `requirements-dev.txt` o la configuración del frontend
- [ ] `.github/workflows/ci.yml`
- [ ] `backend/.env.example`

## Referencias

- HU-066 en [`historias-de-usuario.md`](../aidlc/inputs/historias-de-usuario.md).
- Unidad [cierre-de-mes](../aidlc/units/cierre-de-mes.md).
