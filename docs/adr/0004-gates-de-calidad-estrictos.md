# ADR-0004 — Exigir gates de calidad estrictos desde el inicio

- **Estado:** Aceptado
- **Fecha:** 2026-10-16
- **Decidido por:** Juan Diego
- **Módulos afectados:** infra, frontend, docs

---

## Contexto

Las reglas de negocio de Big Media cambian seguido y varias son todavía provisorias. Un cambio en una regla puede romper algo lejano, y lo más crítico del sistema (la disponibilidad de carteles y la confirmación de reservas) depende de transacciones de PostgreSQL que un entorno distinto puede ocultar.

Hasta ahora el código existente no tenía verificación automática de formato, tipos ni cobertura, y los tests de base de datos eran opcionales (`BIGMEDIA_RUN_DB_TESTS`). Es más barato empezar con el listón alto que subirlo después sobre código ya escrito.

## Decisión

> Vamos a exigir en el CI ruff, mypy en modo estricto, coverage mínimo de 80 %, tests siempre contra PostgreSQL, gitleaks y verificación de migraciones y de despliegue.

- **ruff** con las reglas de CheatSheet más `DJ` y `PGH`: `E`, `W`, `F`, `I`, `UP`, `B`, `S`, `ANN`, `PT`, `C90`, `SIM`, `RET`, `ARG`, `PTH`, `DTZ`, `T20`, `BLE`, `RUF`, `DJ`, `PGH`. Línea de 100 caracteres y Python 3.12.
- **mypy `--strict`** con `django-stubs` y `djangorestframework-stubs`.
- **Coverage mínimo de 80 %** en el backend (sentencias y ramas) y en el frontend (líneas y sentencias).
- **Tests siempre contra PostgreSQL**, local con Docker Compose y en CI con un service container. Desaparece `BIGMEDIA_RUN_DB_TESTS` y el job falla si algún test queda salteado.
- **gitleaks**, **`makemigrations --check`** y **`check --deploy --fail-level WARNING`**.
- **Bajar un umbral requiere un ADR nuevo.**

### Decisiones de configuración

- **`RUF012` ignorado.** Django y DRF declaran listas mutables como atributos de clase (`Meta.ordering`, `fields`, `permission_classes`). Pasarlas a tuplas cambia las opciones de los modelos y genera migraciones; anotarlas con `ClassVar` agrega ruido.
- **Migraciones excluidas de ruff y mypy.** Es código generado y el único archivo excluido de las herramientas.
- **Excepciones en tests.** Se permiten `S101`, `S105`, `S106` y `S603` (subprocesos con `sys.executable` en los tests de settings de producción), y las anotaciones son opcionales. mypy relaja `disallow_untyped_defs`, `disallow_incomplete_defs` y `disallow_untyped_calls` solo en `tests.*`.
- **`security.W005` y `security.W021` silenciados solo en producción.** El dominio es un subdominio de `onrender.com` que no controlamos y el preload de HSTS es difícil de revertir. Se revisa si se usa un dominio propio.
- **`PGH` en ruff y `ignore-without-code` en mypy.** Ruff suma `PGH003` (`type: ignore` genérico) y `PGH004` (`noqa` genérico); mypy habilita `enable_error_code = ["ignore-without-code"]`, que `strict` no incluye. Así ningún `type: ignore` queda sin código y ningún `# noqa` es general.
- **Frontend: el umbral de 80 % aplica a líneas y sentencias.** Funciones y ramas se informan sin umbral.
- **"Sin `any` explícito ni `@ts-ignore`" en TypeScript** lo verifica la revisión del PR, no una herramienta.

## Alternativas consideradas

| Alternativa | Ventajas | Por qué se descartó |
| --- | --- | --- |
| Gates graduales: mypy no estricto y coverage de 70 % | Menos arreglos de código al empezar | Descartada por elección de Juan Diego: cuando las reglas cambian seguido, los tests y los tipos son la red que avisa qué se rompió, y un listón bajo es difícil de subir después |
| Gates básicos: ruff y tests, sin mypy | Mínimo esfuerzo y CI rápido | Descartada por la misma razón: sin tipos, un cambio de regla rompe código lejano sin aviso |
| Tests de base de datos opcionales | Más cómodo para quien no levanta PostgreSQL | Una regla de disponibilidad podría pasar en un modo de ejecución y fallar en otro |

## Consecuencias

**Positivas**
- Un cambio de regla que rompe algo lejano se detecta en el PR, no en producción.
- Los tests corren en el mismo motor que producción.
- Ninguna regla se desactiva en silencio: ni `type: ignore` ni `# noqa` sin código.

**Negativas / costo que aceptamos**
- El PR `chore/gates-de-calidad` incluye arreglos de código para que lo existente pase los gates.
- Hace falta PostgreSQL local para correr la suite, y el CI es más lento.
- Actualizar las versiones fijas de las herramientas es un cambio deliberado, en su propio PR.

**Qué se vuelve más difícil**
- Hacer un cambio rápido sin tipos ni tests.
- Bajar un umbral: requiere un ADR nuevo que reemplace a este.

## Impacto en las reglas del repositorio

- [x] `CLAUDE.md`
- [x] `docs/estandares-de-codigo.md`
- [x] `pyproject.toml`, `requirements-dev.txt` o la configuración del frontend
- [x] `.github/workflows/ci.yml`
- [ ] `backend/.env.example`
- [ ] Ninguna

## Referencias

- [`../estandares-de-codigo.md`](../estandares-de-codigo.md)
- [`../gestion-de-configuracion.md`](../gestion-de-configuracion.md)
- [ADR-0002](0002-gitflow-con-develop.md)
