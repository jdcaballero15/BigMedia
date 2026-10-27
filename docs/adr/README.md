# ADR — Registros de decisiones de arquitectura

Un **ADR** documenta una decisión técnica importante: qué se decidió, por qué y qué se descartó.

Existe para que, dentro de seis meses, o cuando un agente nuevo abra el repositorio, nadie tenga que adivinar por qué las cosas son como son ni volver a discutir algo que ya se resolvió.

## Cuándo escribir uno

Si la decisión **afecta a más de un módulo** o **es cara de revertir**, necesita un ADR.

- Elegir un framework, un ORM o un motor de base de datos.
- Patrón de arquitectura y estructura de carpetas.
- Esquema de autenticación y autorización.
- Estrategia de colas, reintentos o idempotencia.
- Crear una carpeta nueva en la raíz del repositorio.
- Cambiar una regla de [`../estandares-de-codigo.md`](../estandares-de-codigo.md) o de [`CLAUDE.md`](../../CLAUDE.md).
- Cambiar el modelo de ramas o los entornos.

No hace falta un ADR para: nombrar una función, agregar un test, corregir un bug.

**Los cambios de reglas de negocio no llevan ADR**, salvo que cambien la arquitectura o una regla de `CLAUDE.md`. Esos cambios se registran en el catálogo [`reglas-de-negocio.md`](../aidlc/reglas-de-negocio.md) (ver [ADR-0003](0003-requisitos-evolutivos.md)).

## Cómo

1. Copiá [`0000-plantilla.md`](0000-plantilla.md) a `NNNN-titulo-en-kebab.md`, donde `NNNN` es el siguiente número libre.
2. Escribilo en estado `Propuesto` y abrí el PR.
3. Cuando el PR se aprueba, pasa a `Aceptado`.

## Reglas

- **Un ADR aceptado nunca se edita ni se borra.** Si la decisión cambia, se escribe uno nuevo que lo *reemplaza* y se enlazan entre sí.
- Un ADR describe el **contexto y el porqué**, no el cómo. El cómo vive en el código.
- Si no podés nombrar al menos una alternativa que descartaste, probablemente no tomaste una decisión: juntaste una suposición.

## Índice

| # | Título | Estado | Fecha |
| --- | --- | --- | --- |
| [0001](0001-estructura-del-repositorio.md) | Organizar el repositorio como monolito modular Django | Aceptado | 2026-10-16 |
| [0002](0002-gitflow-con-develop.md) | Usar GitFlow con `develop` | Aceptado | 2026-10-16 |
| [0003](0003-requisitos-evolutivos.md) | Tratar requisitos y reglas de negocio como insumos vivos | Aceptado | 2026-10-16 |
| [0004](0004-gates-de-calidad-estrictos.md) | Exigir gates de calidad estrictos desde el inicio | Aceptado | 2026-10-16 |
| [0005](0005-base-de-staging-en-neon.md) | Usar Neon para la base de staging y Render pago para producción | Propuesto | 2026-10-21 |
| [0006](0006-interacciones-en-campanias.md) | Ubicar las interacciones comerciales en la app `campanias` | Propuesto | 2026-10-27 |
