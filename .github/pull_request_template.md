## Descripción

<!-- Qué resuelve este PR y por qué. -->

Closes #

## Módulos afectados

- [ ] `usuarios` — [ ] `inventario` — [ ] `clientes` — [ ] `campanias`
- [ ] `reservas` — [ ] `costos` — [ ] `facturacion` — [ ] `auditoria`
- [ ] `frontend` — [ ] `infra` — [ ] `docs`

## Tipo de cambio

- [ ] `feature/` — funcionalidad nueva
- [ ] `fix/` — corrección
- [ ] `docs/` — documentación, historias o reglas
- [ ] `chore/` — mantenimiento o configuración
- [ ] `hotfix/` — urgencia en `main`

## Reglas de negocio

- Reglas que este PR aplica o cambia: <!-- RN-xxx, o "ninguna" -->
- [ ] Si es un PR `docs/historias-…` que cambia una historia o una regla, hay fila en `docs/aidlc/inputs/registro-de-cambios.md`
- [ ] Si es un PR de código que aplica una regla, solo se actualizó su columna "Dónde vive" en `docs/aidlc/reglas-de-negocio.md` (el valor o el estado de una regla cambian en un PR `docs/historias-…`)
- [ ] Los tests nuevos que verifican una regla llevan `@pytest.mark.regla("RN-xxx")`

## Definition of Done

- [ ] `ruff format --check . && ruff check .`
- [ ] `mypy backend`
- [ ] `pytest --cov` en verde y coverage ≥ 80 %
- [ ] Ningún test salteado
- [ ] `python backend/manage.py makemigrations --check --dry-run`
- [ ] Frontend: `format:check`, `lint`, `typecheck`, `test:coverage`, `build`
- [ ] gitleaks sin hallazgos
- [ ] La rama sigue el formato y apunta a la base correcta
- [ ] Los commits siguen Conventional Commits

## Seguridad

- [ ] Sin credenciales, tokens ni secretos en el código
- [ ] Sin datos personales reales (ni en código, ni en tests, ni en logs)
- [ ] Si hay variables nuevas, se actualizó `backend/.env.example`

## Calidad y decisiones

- [ ] Tests agregados o actualizados
- [ ] Si es un bug, incluye primero el test que lo reproduce
- [ ] Si hubo una decisión técnica, hay ADR en `docs/adr/`
- [ ] No se desactivó ninguna regla para pasar CI

## Cómo se verificó

<!-- Comandos y resultado, o capturas para cambios de interfaz. -->
