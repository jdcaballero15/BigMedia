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

- **Origen:** una épica del roadmap o un issue triado.
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
- Actualizá `docs/aidlc/units.md`: `en revisión` y, al mergear, `mergeada`.
- Actualizá `docs/aidlc/reglas-de-negocio.md` si cambió una regla.

## 8. Triage de pedidos

Cada issue `pedido` termina en una de cuatro salidas:

1. Cambia una regla.
2. Historia nueva o ajustada.
3. Bug.
4. Descartado, con motivo.

El issue se etiqueta y, si se acepta, se convierte en una unidad.

## 9. Diferencias con el AI-DLC original de CheatSheet

- Historias y reglas son insumos vivos: cambian por PR `docs/` con registro, sin ADR.
- El roadmap es corto y se reordena; no reparte todo el catálogo al inicio.
- Una unidad mergeada es histórico inmutable; los cambios posteriores son unidades de ajuste `ajuste-<tema>`.
- El plan de unidad es de una página.
