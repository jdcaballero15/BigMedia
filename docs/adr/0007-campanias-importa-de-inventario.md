# ADR-0007 — Permitir que `campanias` importe de `inventario`

- **Estado:** Propuesto
- **Fecha:** 2026-10-27
- **Decidido por:** Gonza
- **Módulos afectados:** campanias, inventario, docs

---

## Contexto

HU-055 pide que la campaña lleve líneas de formato con la cantidad de posiciones solicitadas. La
tabla de apps de `CLAUDE.md` ya pone "posiciones por formato" en `campanias`, pero la tabla de
dependencias solo le permite importar de `clientes`. Como la línea tiene que apuntar a
`inventario.Formato`, no puede vivir en `campanias` sin cambiar esa tabla.

## Decisión

> Vamos a permitir que `campanias` importe de `inventario`.

El modelo `LineaFormato` vive en `campanias` y apunta a `inventario.Formato` con `PROTECT`. El
seguimiento de solicitado, reservado y faltante (HU-058) se calcula en `reservas`, que ya puede
importar de `campanias` y de `inventario`. La implementación entra en la unidad
[posiciones-por-formato](../aidlc/units/posiciones-por-formato.md).

## Alternativas consideradas

| Alternativa | Ventajas | Por qué se descartó |
| --- | --- | --- |
| Modelo en `reservas` | No cambia la tabla de dependencias | La línea es parte de la definición comercial de la campaña, no de una reserva; contradice la responsabilidad de `campanias` |
| Guardar el formato en `campanias` como ID sin FK | No agrega dependencia | Pierde la integridad referencial y el `PROTECT` sobre el formato |

## Consecuencias

**Positivas**
- La campaña y su pedido por formato quedan juntos.
- `inventario` sigue sin importar de ninguna app, así que no hay ciclo.

**Negativas / costo que aceptamos**
- `campanias` deja de depender solo de `clientes`.

**Qué se vuelve más difícil**
- Nada relevante: `inventario` es una hoja del grafo de dependencias.

## Impacto en las reglas del repositorio

- [x] `CLAUDE.md`: la tabla de §2 suma `inventario` a lo que puede importar `campanias`.
- [ ] `docs/estandares-de-codigo.md`
- [ ] `pyproject.toml`, `requirements-dev.txt` o la configuración del frontend
- [ ] `.github/workflows/ci.yml`
- [ ] `backend/.env.example`

## Referencias

- HU-055 y HU-058 en [`historias-de-usuario.md`](../aidlc/inputs/historias-de-usuario.md).
- Unidad [posiciones-por-formato](../aidlc/units/posiciones-por-formato.md).
- [`docs/arquitectura.md`](../arquitectura.md#3-apps-del-backend).
