# Flujo de trabajo

**Todos los cambios al repositorio se integran mediante Pull Request (PR) contra `main`.** No se hacen commits ni pushes directos a `main`, incluso para documentación o correcciones pequeñas. Cada trabajo se desarrolla en una rama propia.

## Pasos

1. Actualizá `main` y creá una rama descriptiva, por ejemplo `feat/inventario` o `fix/filtro-zona`.
2. Hacé commits acotados a esa tarea. Si otra persona trabaja en paralelo, conservá sus archivos y commits fuera de tu rama.
3. Ejecutá las pruebas y comprobaciones que correspondan al cambio. Para cambios en la API: `python -m pytest backend/tests -q` y `python backend/manage.py check`, con PostgreSQL disponible. Para cambios en la web, desde `frontend/`: `npm test`, `npm run lint` y `npm run build`.
4. Subí la rama (`git push -u origin nombre-de-rama`) y abrí un PR hacia `main`. Describí el cambio, cómo lo verificaste, las decisiones pendientes y cualquier limitación.
5. Revisá el diff y resolvé los comentarios y controles del PR antes de integrarlo. No uses `--force` para resolver un rechazo de push sin coordinarlo con el equipo.

Si GitHub permite configurar reglas de rama, protegé `main` con **Require a pull request before merging** y los controles obligatorios del proyecto. La regla de PR se aplica aunque esa protección aún no esté activada en GitHub.
