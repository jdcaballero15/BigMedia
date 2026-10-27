# ADR-0006 — Ubicar las interacciones comerciales en la app `campanias`

- **Estado:** Propuesto
- **Fecha:** 2026-10-27
- **Decidido por:** Juan Diego y Gonza
- **Módulos afectados:** campanias, clientes, docs

---

## Contexto

`docs/arquitectura.md` ubicaba las interacciones comerciales en `clientes`. HU-020 pide que una
interacción lleve un cliente, una campaña opcional y, si el cliente es intermediario formal, uno
de sus contactos. También pide que se vea en la ficha del cliente y en la de la campaña.

La tabla de dependencias de `CLAUDE.md` permite que `campanias` importe de `clientes`, pero no al
revés. Por eso, con el modelo en `clientes`, la interacción no podía apuntar a la campaña.

## Decisión

> Vamos a ubicar el modelo `Interaccion` en la app `campanias`.

`Interaccion` apunta a `clientes.Cliente`, `clientes.Contacto` y `campanias.Campania`, todas con
`PROTECT`. La API está en `/api/campanias/interacciones/` y se filtra por `cliente` y por
`campania`. La app `clientes` sigue sin importar de ninguna otra. La implementación entró en la
unidad [interacciones](../aidlc/units/interacciones.md) (PR #73).

## Alternativas consideradas

| Alternativa | Ventajas | Por qué se descartó |
| --- | --- | --- |
| Modelo en `clientes`, con FK a `Campania` | Respeta la responsabilidad que figuraba en la arquitectura | Crea una dependencia circular entre `clientes` y `campanias` |
| Modelo en `clientes`, más un vínculo aparte en `campanias` | No cambia la arquitectura ni las dependencias | El alta con campaña cruza dos apps y suma un modelo y una API solo para el vínculo |
| Modelo en `clientes`, sin vínculo a la campaña | Es lo más simple | No cumple el criterio 2 de HU-020 |

## Consecuencias

**Positivas**
- No se agrega ninguna dependencia nueva entre apps.
- Si se confirma RN-018, el vínculo opcional a una marca también se puede agregar desde `campanias`.

**Negativas / costo que aceptamos**
- La ficha del cliente, en `features/clientes`, muestra un componente de `features/campanias`.

**Qué se vuelve más difícil**
- Encontrar las interacciones: quien las busque en `clientes` tiene que ir a la tabla de apps de
  `docs/arquitectura.md`.

## Impacto en las reglas del repositorio

- [x] `CLAUDE.md`: la tabla de apps de §2 suma las interacciones a `campanias`.
- [ ] `docs/estandares-de-codigo.md`
- [ ] `pyproject.toml`, `requirements-dev.txt` o la configuración del frontend
- [ ] `.github/workflows/ci.yml`
- [ ] `backend/.env.example`

## Referencias

- HU-020 y HU-068 en [`historias-de-usuario.md`](../aidlc/inputs/historias-de-usuario.md).
- Unidad [interacciones](../aidlc/units/interacciones.md) y PR #73.
- [`docs/arquitectura.md`](../arquitectura.md#3-apps-del-backend).
