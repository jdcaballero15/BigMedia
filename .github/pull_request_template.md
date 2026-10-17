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
- [ ] Si cambió una regla, se actualizó `docs/aidlc/reglas-de-negocio.md` (y el registro de cambios si cambió una historia)
- [ ] Los tests nuevos que verifican una regla llevan `@pytest.mark.regla("RN-xxx")`

## Definition of Done

- [ ] `ruff format --check . && ruff check .`
- [ ] `mypy backend`
- [ ] `pytest` en verde y coverage ≥ 80 %
- [ ] `python backend/manage.py makemigrations --check --dry-run`
- [ ] Frontend: `format:check`, `lint`, `typecheck`, `test:coverage`, `build`
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
