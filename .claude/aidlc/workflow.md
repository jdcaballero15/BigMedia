# Workflow AI-DLC: pasos y plantillas

Complementa `.claude/aidlc/AIDLC.md` (gates y reglas no negociables). Se carga al empezar trabajo de desarrollo.

## 1. Insumos y su estado

| Insumo | Estado | Cómo cambia |
| --- | --- | --- |
| `docs/arquitectura.md` y `docs/adr/` | decidido | Por ADR nuevo |
| `CLAUDE.md` y `docs/estandares-de-codigo.md` | decidido | Por PR `docs/` |
| `docs/gestion-de-configuracion.md` | decidido | Por PR `docs/` |
| `docs/aidlc/inputs/historias-de-usuario.md` | **vivo** | Por PR `docs/` con entrada en `registro-de-cambios.md` |
| `docs/aidlc/reglas-de-negocio.md` | **vivo** | Por PR `docs/` con entrada en `registro-de-cambios.md` |

## 2. Documentos de trabajo

```text
docs/aidlc/
├── roadmap.md              # corto y reordenable: épica actual, próximas y "más adelante"
├── units.md                # mapa de unidades y su estado (pendiente, en curso, en revisión, mergeada)
├── reglas-de-negocio.md    # catálogo vivo de reglas RN-xxx
├── inputs/                 # historias, registro de cambios, importación y UX
└── units/<unidad>.md       # plan de una página y registro de gates de cada unidad
```

## 3. Paso 0 (Origen) y Paso 1 (Encuadre), sin gate

- **Origen:** una épica del roadmap o un issue triado (ver §8).
- **Encuadre:** leé las historias, las reglas y el registro de cambios involucrados. Decí en tres líneas: app dueña, capas que toca, y si hay migraciones o reglas nuevas.
- Si la app dueña no está clara, preguntá en español con opciones concretas.

## 4. Paso 2: Gate 1, plan de unidad

Agregá la fila a `docs/aidlc/units.md` si no existe, y creá `docs/aidlc/units/<unidad>.md` con esta plantilla:

```markdown
# Unidad: <nombre>

- **Estado:** en curso · **Épica:** <épica> · **App dueña:** <app>
- **Origen:** <HU-xxx / RN-xxx / issue #N> · **Rama:** `<tipo>/<modulo>-<descripcion>`

## Objetivo
<Una o dos oraciones.>

## Cambios
- <app>: <qué cambia>

## Migraciones
<Ninguna / cuáles y si mueven datos.>

## Reglas provisorias que se usan
<RN-xxx con su valor actual, o "ninguna".>

## Cómo se prueba
- <tests nuevos, con su marcador de regla si aplica>

## Registro de gates
- Gate 1 (plan): <fecha> — <aprobado por>
- Gate 2 (verificación): <fecha> — <salida resumida de los comandos>
- Gate 3 (PR): <número de PR>
```

Parate acá hasta que Juan Diego apruebe.

## 5. Paso 3: Implementación

- TDD: primero el test que falla.
- Los tests que verifican una regla llevan `@pytest.mark.regla("RN-xxx")`.
- Lo provisorio se implementa como parámetro configurable cuando sea posible.
- Commits en Conventional Commits.

## 6. Paso 4: Gate 2, verificación

Corré los mismos comandos de la Definition of Done de `CLAUDE.md` §7 y pegá la salida real en el registro de gates del plan. Esperá a Juan Diego.

## 7. Paso 5: Gate 3, PR

Solo cuando se pida:

- Completá la plantilla de PR y agregá `Closes #N` si hay issue.
- Actualizá `docs/aidlc/units.md`: `en revisión` al abrir el PR, y `mergeada` en el último commit del mismo PR, antes del merge. Si se olvidó, va en el próximo PR `docs/`.
- Si la unidad aplica una regla, actualizá en `docs/aidlc/reglas-de-negocio.md` solo la columna "Dónde vive" y sus tests. El valor o el estado de la regla y la entrada del registro de cambios van en un PR `docs/historias-<descripcion>` (ver §9).

## 8. Triage de pedidos

Cada issue `pedido` termina en una de cuatro salidas, cada una con su etiqueta de salida:

| Salida | Etiqueta de salida |
| --- | --- |
| 1. Cambia una regla | `regla` |
| 2. Historia nueva o ajustada | se queda con `pedido`, más un comentario que enlaza el PR `docs/historias-<descripcion>` |
| 3. Bug | `bug` |
| 4. Descartado, con motivo | `descartado` |

Un issue está **triado** cuando su salida está anotada en un comentario y lleva su etiqueta de salida. Un issue que solo tiene `pedido`, sin ese comentario, todavía no está triado. Si se acepta, se convierte en una unidad.

## 9. Cambiar una historia o una regla

- El cambio va en un PR `docs/historias-<descripcion>`, sin código, con una fila en `docs/aidlc/inputs/registro-de-cambios.md`. Ahí se cambian el valor y el estado de una regla.
- Un PR de código que aplica una regla solo actualiza la columna "Dónde vive" de esa regla y sus tests.
- Los IDs (`HU-xxx`, `RN-xxx`) nunca se reutilizan ni se renumeran. Una historia nueva toma el siguiente número libre; una eliminada se marca `(retirada AAAA-MM-DD: motivo)` y una fusionada, `(fusionada en HU-xxx)`.
- Si el cambio mueve historias entre épicas o afecta unidades, el mismo PR actualiza `docs/aidlc/roadmap.md` y `docs/aidlc/units.md`.
- Cuando se toca una historia, sus reglas se referencian por ID (`RN-xxx`) en lugar de repetirse. No se reescribe el documento completo por adelantado.

## 10. Diferencias con el AI-DLC original de CheatSheet

- Historias y reglas son insumos vivos: cambian por PR `docs/` con registro, sin ADR.
- El roadmap es corto y se reordena; no reparte todo el catálogo al inicio.
- Una unidad mergeada es histórico inmutable; los cambios posteriores son unidades de ajuste `ajuste-<tema>`.
- El plan de unidad es de una página.
