# ADR-0005 — Usar Neon para la base de staging y Render pago para producción

- **Estado:** Propuesto
- **Fecha:** 2026-10-21
- **Decidido por:** Juan Diego
- **Módulos afectados:** infra, docs

---

## Contexto

La base gratis de producción en Render vence el 17/11/2026, y la unidad [entornos](../aidlc/units/entornos.md)
dejó definidos dos entornos: producción (`main`) y staging (`develop`). El plan era tener las dos bases
en Render, pero:

- Render permite **una sola base gratis por workspace**, y la base gratis **vence a los 30 días**:
  staging habría que recrearlo todos los meses.
- Render no tiene visor de tablas ni editor SQL en su panel.
- El presupuesto es chico: staging tiene que costar cero, y producción tiene que ser estable, con
  copias de seguridad y costo previsible.

Costos estimados a octubre de 2026 (fuentes de terceros, a confirmar en cada panel): Render web
Starter ~USD 7/mes, Render PostgreSQL Basic-256mb ~USD 6/mes más disco; Neon Free USD 0 sin
vencimiento (0,5–1 GB, 100 horas de cómputo por mes); Neon Launch por uso (~USD 5–15/mes para una app
chica).

## Decisión

> Vamos a usar Render pago (web Starter y PostgreSQL Basic-256mb) para producción, y Neon Free para la
> base de staging, con la web de staging en Render gratis.

- Producción: `bigmedia-web` y `bigmedia-db` en planes pagos, declarados en `render.yaml`. Copias de
  seguridad con la recuperación de Render (3 días en el workspace Hobby).
- Staging: proyecto Neon en AWS us-east-1 (Virginia, la región de Render). La web de staging recibe la
  URL **directa** de Neon (sin pooler, con `sslmode=require`) como `DATABASE_URL`, cargada a mano en
  el panel de Render (`sync: false`). Nunca se guarda en Git.
- Los esquemas se siguen cambiando solo con migraciones de Django; nunca a mano en ninguna base.

## Alternativas consideradas

| Alternativa | Ventajas | Por qué se descartó |
| --- | --- | --- |
| Las dos bases en Render (staging gratis) | Un solo proveedor; `render.yaml` conecta la base solo | Solo una base gratis por workspace y vence a los 30 días: staging habría que recrearlo cada mes |
| Staging en Render con base paga | Sin vencimiento, un solo proveedor | ~USD 6/mes más solo para pruebas |
| Las dos bases en Neon | Visor de tablas y ramas de base también en producción; costo similar | Producción sale de la red interna de Render por internet (más demora y base expuesta); costo por uso, menos previsible; otro proveedor crítico para producción |

## Consecuencias

**Positivas**
- Staging cuesta cero y no vence; los datos de ejemplo se cargan una sola vez.
- Neon tiene editor SQL y visor de tablas para explorar el esquema en staging.
- Producción queda en la red interna de Render, con costo fijo y copias de seguridad.

**Negativas / costo que aceptamos**
- Un proveedor más (cuenta de Neon) que administrar.
- Producción cuesta ~USD 13/mes.
- La web de staging conecta a Neon por internet: algo más de demora y un arranque lento cuando la base
  de Neon se duerme.

**Qué se vuelve más difícil**
- La `DATABASE_URL` de staging se carga a mano en Render; si se rota la contraseña en Neon, hay que
  actualizarla en el panel.
- Staging y producción corren en motores administrados distintos: una diferencia de configuración
  de Postgres puede aparecer solo en uno de los dos.

## Impacto en las reglas del repositorio

- [ ] `CLAUDE.md`
- [ ] `docs/estandares-de-codigo.md`
- [ ] `pyproject.toml`, `requirements-dev.txt` o la configuración del frontend
- [ ] `.github/workflows/ci.yml`
- [ ] `backend/.env.example`
- [x] Ninguna (cambia `render.yaml` y `docs/operacion/despliegue-render.md`)

## Referencias

- [ADR-0002](0002-gitflow-con-develop.md) — GitFlow con `develop`.
- Unidades [entornos](../aidlc/units/entornos.md) y [ajuste-entornos-neon](../aidlc/units/ajuste-entornos-neon.md).
- [Despliegue en Render](../operacion/despliegue-render.md).
- Precios: [neon.com/pricing](https://neon.com/pricing) y panel de Render.
