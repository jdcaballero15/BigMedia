# ADR-0002 — Usar GitFlow con `develop`

- **Estado:** Aceptado
- **Fecha:** 2026-10-16
- **Decidido por:** Juan Diego
- **Módulos afectados:** infra, docs

---

## Contexto

Render despliega `main` automáticamente cuando el CI pasa (`autoDeployTrigger: checksPass`). Antes de esta decisión, todo el trabajo se integraba directo a `main`, de modo que cada cambio integrado era un cambio en producción.

Los requisitos del negocio cambian con el uso (ver [ADR-0003](0003-requisitos-evolutivos.md)) y hay más de una persona trabajando en paralelo. Hace falta un lugar donde los cambios se integren y se prueben juntos antes de llegar a producción.

## Decisión

> Vamos a usar GitFlow con una rama `develop`: los cambios se integran a `develop` y `main` solo recibe lo que está listo para producción.

| Tipo | Patrón | Destino |
| --- | --- | --- |
| Funcionalidad | `feature/<modulo>-<descripcion>` | `develop` |
| Corrección | `fix/<modulo>-<descripcion>` | `develop` |
| Documentación | `docs/<descripcion>` | `develop` |
| Mantenimiento | `chore/<descripcion>` | `develop` |
| Emergencia | `hotfix/<descripcion>` | `main`, y después merge a `develop` |
| Release | `develop` | `main` |

- `main` es producción y despliega en Render; `develop` integra y solo corre CI.
- **Hotfix:** rama `hotfix/<descripcion>` desde `main` y PR hacia `main`. Una vez integrado, se crea `chore/infra-sincronizar-main-<AAAAMMDD>` desde `main` y se abre un PR hacia `develop` para no perder el arreglo. El job `convenciones` del CI rechaza PRs desde `main` o `hotfix/*` hacia `develop`, por eso la sincronización va en una rama `chore/`.
- Los detalles operativos están en [`gestion-de-configuracion.md`](../gestion-de-configuracion.md).

### Staging: no se implementa

No existe entorno de staging. Esto es lo que haría falta para sumarlo:

- Un servicio web y una base de datos en Render conectados a `develop`.
- Un segundo Blueprint, o un servicio adicional en `render.yaml`.
- Un job `deploy-staging` en `.github/workflows/ci.yml` con `needs:` sobre todos los gates y `if: github.ref == 'refs/heads/develop'`.
- Los secretos del despliegue cargados en GitHub.

Conviene activarlo cuando Seba empiece a probar cambios antes de que lleguen a producción. Al hacerlo, se escribe un ADR nuevo que reemplace a este en lo que cambie.

## Alternativas consideradas

| Alternativa | Ventajas | Por qué se descartó |
| --- | --- | --- |
| Trunk: todo a `main` | Menos ramas y menos ceremonia | Descartada por elección de Juan Diego: se prefiere separar la integración de la producción, para que un cambio no llegue a Render hasta que se decide hacer un release |
| GitFlow con staging desde el inicio | Probar en un entorno parecido a producción | Suma costo y operación (segundo servicio y base en Render) sin que todavía haya quien pruebe ahí; queda documentado como siguiente paso |

## Consecuencias

**Positivas**
- Producción solo cambia con un release explícito (`develop` → `main`) o un hotfix.
- Los cambios se integran y se prueban juntos en `develop` antes de llegar a producción.

**Negativas / costo que aceptamos**
- Una rama más que mantener y un paso extra (el PR de release).
- Los hotfix exigen una sincronización posterior hacia `develop`.

**Qué se vuelve más difícil**
- Entregar un cambio urgente a producción: pasa por hotfix o por un release.
- Evitar que `develop` y `main` diverjan si se olvida la sincronización de un hotfix.

## Impacto en las reglas del repositorio

- [x] `CLAUDE.md`
- [ ] `docs/estandares-de-codigo.md`
- [ ] `pyproject.toml`, `requirements-dev.txt` o la configuración del frontend
- [x] `.github/workflows/ci.yml`
- [ ] `backend/.env.example`
- [ ] Ninguna

## Referencias

- [`../gestion-de-configuracion.md`](../gestion-de-configuracion.md)
- [`../operacion/despliegue-render.md`](../operacion/despliegue-render.md)
- [ADR-0001](0001-estructura-del-repositorio.md)
