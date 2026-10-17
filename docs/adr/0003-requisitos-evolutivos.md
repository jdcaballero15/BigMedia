# ADR-0003 — Tratar requisitos y reglas de negocio como insumos vivos

- **Estado:** Aceptado
- **Fecha:** 2026-10-16
- **Decidido por:** Juan Diego
- **Módulos afectados:** docs

---

## Contexto

El relevamiento con Big Media quedó incompleto: hay reglas de negocio todavía sin confirmar (por ejemplo, el día límite entre reservas). Además, el sistema se va a ajustar con el uso de Seba, y sus pedidos llegan por WhatsApp y por llamadas, sin un formato fijo.

Un proceso que trata las historias de usuario como insumos cerrados no sirve acá: cada pedido obligaría a un trámite pesado, o peor, a cambios que no dejan registro.

## Decisión

> Vamos a tratar las historias y las reglas de negocio como documentos vivos, con IDs estables y un registro de cambios, y los pedidos entran como issues.

- **Catálogo de reglas:** [`reglas-de-negocio.md`](../aidlc/reglas-de-negocio.md), una tabla con IDs `RN-xxx` que nunca se reutilizan y estados `pendiente`, `provisoria`, `confirmada` o `reemplazada por RN-xxx`. Lo `provisoria` se implementa como parámetro configurable cuando se puede.
- **Historias vivas:** `docs/aidlc/inputs/historias-de-usuario.md` es la fuente de verdad. Los IDs `HU-xxx` no se reutilizan ni se renumeran, y cada cambio deja una entrada en `docs/aidlc/inputs/registro-de-cambios.md`.
- **Pedidos:** se cargan como issues con la plantilla "Pedido de Seba" y se clasifican en una de cuatro salidas: cambia una regla, es una historia nueva o ajustada, es un bug o se descarta con motivo. El PR que lo resuelve lo cierra con `Closes #N`.
- **Unidades de ajuste:** los cambios chicos se planifican como unidades `ajuste-<tema>`.
- **Roadmap corto:** [`roadmap.md`](../aidlc/roadmap.md) lista la épica actual y las dos o tres siguientes, y se reordena cuando cambian las prioridades.
- Los cambios de reglas de negocio no llevan ADR salvo que cambien la arquitectura o una regla de `CLAUDE.md`.

El detalle del flujo está en [`AIDLC.md`](../../.claude/aidlc/AIDLC.md) y [`workflow.md`](../../.claude/aidlc/workflow.md).

## Alternativas consideradas

| Alternativa | Ventajas | Por qué se descartó |
| --- | --- | --- |
| AI-DLC de CheatSheet: insumos de solo lectura y un ADR por cada cambio de historia | Máxima trazabilidad y decisiones inmutables | Demasiado pesado para cambios frecuentes: un ajuste chico exigiría un ADR |
| `feedback.md` en el repositorio | Todo queda junto al código | Anotar un pedido exigiría abrir un PR |
| Notion u otra herramienta externa | Captura rápida y cómoda | Separa el pedido del PR que lo resuelve y se pierde la trazabilidad |

## Consecuencias

**Positivas**
- Un pedido se registra en minutos y queda la traza pedido → PR → regla o test.
- Lo provisorio no frena el desarrollo y se puede cambiar sin desplegar código.
- Buscar un ID encuentra todo lo afectado por un cambio.

**Negativas / costo que aceptamos**
- Hay que mantener al día el catálogo, el registro de cambios, el roadmap y las unidades.
- Los documentos de insumo cambian con el tiempo, así que no sirven como foto fija de lo acordado al inicio.

**Qué se vuelve más difícil**
- Reconstruir qué se había pedido originalmente sin leer el registro de cambios.
- Mantener la disciplina de los IDs estables a medida que crecen las historias.

## Impacto en las reglas del repositorio

- [x] `CLAUDE.md`
- [ ] `docs/estandares-de-codigo.md`
- [x] `pyproject.toml`, `requirements-dev.txt` o la configuración del frontend
- [ ] `.github/workflows/ci.yml`
- [ ] `backend/.env.example`
- [ ] Ninguna

El marcador de pytest `regla("RN-xxx")` se declara en `pyproject.toml`.

## Referencias

- [`../aidlc/reglas-de-negocio.md`](../aidlc/reglas-de-negocio.md)
- [`../aidlc/roadmap.md`](../aidlc/roadmap.md)
- [`../aidlc/units.md`](../aidlc/units.md)
- [`AIDLC.md`](../../.claude/aidlc/AIDLC.md) y [`workflow.md`](../../.claude/aidlc/workflow.md)
- [ADR-0002](0002-gitflow-con-develop.md)
