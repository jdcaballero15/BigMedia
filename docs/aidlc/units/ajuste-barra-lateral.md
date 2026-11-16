# Unidad: ajuste-barra-lateral

- **Estado:** en revisión · **Épica:** E12 Rediseño visual · **App dueña:** `frontend`
- **Origen:** pedido de Juan Diego (2026-11-16), HU-001 y HU-007 ajustadas en el PR #131 ·
  **Rama:** `fix/frontend-ocultar-parametros-auditoria`

## Objetivo

Las pantallas Parámetros y Auditoría no suman al uso diario. Se sacan del menú lateral sin borrar
su código ni el del servidor, para poder volver a mostrarlas con un cambio chico.

## Cambios

- `App.tsx`:
  - Se sacan las entradas `parametros` (sección Configuración) y `auditoria` (sección
    Administración) de `sections`, sus valores del tipo `Page` y los imports de `ParametrosPage`,
    `AuditoriaPage`, `SlidersHorizontal` y `ScrollText`.
  - Configuración queda solo con Catálogos y Administración, solo con Usuarios.
- `features/reservas/ParametrosPage.tsx` y `features/auditoria/Auditoria.tsx`: no se tocan. Siguen
  con sus tests propios, así que el coverage no baja.
- `App.test.tsx`:
  - Los tests "oculta Auditoría a quien no es gerencia" y "muestra Auditoría a gerencia" pasan a
    uno solo: Auditoría no aparece en el menú, ni para gerencia.
  - "muestra Usuarios, Parámetros e Importar carteles solo al administrador" deja de abrir
    Parámetros y comprueba que no aparece ni para el administrador.
- `docs/manual/manual-de-uso.md`: la tabla del menú, el párrafo de permisos y la sección de
  Auditoría dejan de nombrar esas pantallas. La fila del error de fecha pasada cambia su salida:
  hay que pedírselo al equipo técnico (ver "Consecuencia").
- `docs/aidlc/reglas-de-negocio.md`: en "Dónde vive" de RN-001, RN-002 y RN-012, "(pantalla
  Parámetros)" pasa a "(pantalla Parámetros, fuera del menú)".

## Consecuencia

- Los parámetros quedan con su valor actual y nadie los puede cambiar desde la app. Incluye el
  interruptor "Permitir reservas con fecha pasada" (RN-012): si hay que cargar una reserva vieja,
  se vuelve a mostrar la pantalla o se cambia el valor desde la base.
- La auditoría se sigue registrando en el servidor, pero nadie la puede consultar desde la app.

## Fuera de alcance

- El backend: endpoints, permisos y modelos de `reservas` y `auditoria` quedan igual.
- Agregar URLs propias por pantalla o un acceso escondido a estas pantallas.

## Migraciones

Ninguna.

## Reglas provisorias que se usan

Ninguna cambia de valor. RN-001, RN-002 y RN-012 conservan el valor guardado hoy en
`ParametrosDisponibilidad`.

## Cómo se prueba

- Primero se cambian los tests de `App.test.tsx` y se comprueba que fallan con el menú actual;
  después se cambia `App.tsx` y pasan.
- Los tests de `ParametrosPage` y `Auditoria` siguen pasando sin cambios.
- Verificación completa del frontend (`format:check`, `lint`, `typecheck`, `test:coverage`,
  `build`) y `pre-commit run --all-files`.
- Prueba visual en local: el menú como administrador con Gerencia no muestra Parámetros ni
  Auditoría, y las demás secciones quedan iguales.

## Registro de gates

- Gate 1 (plan): 2026-11-16 — aprobado por Juan Diego
- Gate 2 (verificación): 2026-11-16 — aprobado por Juan Diego. Salida de los comandos:
  - Los 2 tests cambiados fallaban antes del cambio (`2 failed | 26 passed`) y pasan después.
  - Frontend: `format:check` (`All matched files use Prettier code style!`), `lint` y `typecheck`
    sin errores, `test:coverage` con `407 passed` en 51 archivos (sentencias 92,78 %, líneas
    94,79 %), `build` `✓ built in 2.00s`.
  - `pre-commit run --all-files`: todos `Passed`, incluido gitleaks.
  - Backend sin cambios: ruff, mypy y pytest no se volvieron a correr localmente; los corre el CI.
- Gate 3 (PR): #132 (2026-11-16), pedido por Juan Diego
