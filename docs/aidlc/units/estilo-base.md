# Unidad: estilo-base

- **Estado:** en curso · **Épica:** E12 Rediseño visual · **App dueña:** frontend
- **Origen:** pedido de Gonza del 2026-10-28 (probando la app de punta a punta) · **Rama:** `feature/frontend-estilo-base`

## Objetivo

Que toda la aplicación tenga un estilo consistente, prolijo y fácil de leer, elegido por Gonza
sobre maquetas: azul marino con superficies celestes, al estilo de la referencia que pasó, y que
en cada pantalla se lea rápido lo que uno entró a ver (el cliente en Clientes, el cartel en
Carteles, etc.).

Esta unidad cambia **cómo se ve**, no qué hace: ningún dato, regla, endpoint ni flujo cambia.
La reestructura de pantallas puntuales (ficha de cliente como página, calendario, resumen de
ítems, selector de período, parámetros) es la unidad siguiente,
[`pantallas-rediseno`](pantallas-rediseno.md).

## Decisiones de Gonza (sobre maquetas)

1. **Paleta azul**, no la monocromática ni la de vidrio, que también se probaron.
2. **Primera columna destacada** en todas las tablas: es "la base de la hoja". Fondo celeste
   suave y el nombre en azul oscuro y negrita. El resto de la tabla, en blanco.
3. **Tablas con esquinas redondeadas** (no cuadradas) y sin barra de desplazamiento horizontal.
4. **Menú lateral solo con iconos**, con el nombre al pasar el mouse.
5. **Barra superior** con la ruta a la izquierda y la fecha a la derecha.
6. **Acciones de cada fila** (Editar, Inactivar y similares) en un menú de tres puntos; la acción
   principal de la fila (por ejemplo «Ver ficha») queda visible.
7. Lo que se descartó: los temas múltiples, el vidrio, las letras A–Z que agrupaban clientes y la
   lista de una sola línea por cliente.

## Estilo

Valores de partida, a ajustar en la revisión visual sin cambiar la dirección:

| Token | Valor | Uso |
| --- | --- | --- |
| `--azul` | `#13306B` | Botón principal, filtro activo, ítem activo del menú, cifra principal, títulos |
| `--azul-2` | `#1D4189` | Hover del azul |
| `--celeste` | `#EEF3FC` | Superficies: cifras, iconos, primera columna, buscador |
| `--celeste-2` | `#E3EBFA` | Hover de la primera columna y de los ítems |
| `--texto` | `#12305F` | Texto principal |
| `--texto-2` | `#4A5D7E` | Texto secundario de las tablas |
| `--texto-3` | `#8592A8` | Etiquetas en mayúsculas, metadatos, fecha |
| `--borde` | `#E3E9F4` | Bordes de cards, inputs y tablas |
| `--fondo` | degradé de `#F7F9FD` a `#FFFFFF` | Fondo de la página |
| `--ambar` / `--ambar-suave` | `#A35A00` / `#FFF4DD` | **Solo** alertas y pendientes |
| `--error` | rojo actual, pasado a token | Errores de formulario y de API |

- **Tipografía:** Inter (o la del sistema si no está). Etiquetas chicas en mayúsculas con
  `letter-spacing` amplio y en `--texto-3`. Títulos de página de 28 px, en negrita y `--azul`.
- **Formas:** cards de 18 px de radio, botones e inputs de 12 px, filtros tipo píldora. Sombra
  suave azulada (`0 6px 18px rgb(19 48 107 / 6%)`), nunca pesada.
- **Iconos:** los de `lucide-react` que ya se usan, dentro de un círculo `--celeste`.
- **Azul lleno solo para lo principal o elegido:** botón primario, filtro activo, ítem activo,
  la cifra principal de cada pantalla. El ámbar, solo para alertas. Nada de destacar en azul un
  elemento cualquiera.

## Cambios

- `frontend/src/App.css`: se reescribe sobre tokens (`:root` con las variables de arriba); ningún
  color fijo fuera de los tokens. Las clases existentes (`card`, `button-primary`, `button-ghost`,
  `section-heading`, `eyebrow`, `filters`, `table-wrap`, `primary-cell`, `row-actions`,
  `edit-form`, `form-grid`, `empty`, `error`, `notice`, `tabs`, etc.) se conservan y cambian de
  aspecto, así las pantallas toman el estilo sin tocar su JSX.
- **Tablas** (`table-wrap`, `primary-cell`): primera columna en celeste, nombre en azul y negrita,
  en una sola línea; encabezados en mayúsculas chicas; esquinas redondeadas; sin scroll
  horizontal en pantallas de 1280 px o más. En pantallas angostas se ocultan primero las columnas
  secundarias (marcadas con una clase `col-secundaria`) antes de recortar.
- `App.tsx`, menú lateral: solo iconos con el nombre en un tooltip (y en `aria-label`, para no
  perder accesibilidad ni los tests que buscan los ítems por nombre). Los separadores entre grupos
  reemplazan los títulos de grupo. El usuario y «Salir» quedan abajo, como icono.
- `App.tsx`, barra superior nueva: ruta (`Big Media / <grupo> / <pantalla>`) y fecha de hoy en
  formato largo («Miércoles 28 de octubre de 2026»).
- `shared/MenuFila.tsx` (nuevo): botón de tres puntos (`aria-label="Más acciones"`) que abre un menú
  con las acciones secundarias de la fila; cierra con Escape o al hacer clic afuera. Las pantallas
  que hoy tienen `row-actions` con más de una acción pasan las secundarias a este menú.
- Tests: los que buscan «Editar», «Inactivar», etc. abren antes el menú de la fila (un helper
  `abrirAcciones(fila)` en `test-setup` o en `shared/`).
- Manual de uso: la sección «Cómo está organizada la pantalla» describe el menú de iconos, la barra
  superior y el menú de tres puntos.

## Fuera de alcance

- Cualquier cambio de datos, reglas, endpoints o flujos.
- Lo de la unidad `pantallas-rediseno`: ficha de cliente como página, Panel con cifras, selector
  de período de los reportes, resumen de Ítems a facturar, calendario de disponibilidad y
  Parámetros.
- Modo oscuro y selector de temas.
- Librerías nuevas: se usan CSS propio y `lucide-react`, que ya está.

## Migraciones

Ninguna.

## Reglas provisorias que se usan

Ninguna.

## Cómo se prueba

- `MenuFila.test.tsx`: abre y cierra el menú (clic, Escape, clic afuera); ejecuta la acción
  elegida; Lectura no ve acciones de edición (`usePuedeEditar`).
- `App.test.tsx`: el menú de iconos expone cada pantalla por su nombre (`aria-label`); la barra
  superior muestra la ruta de la pantalla activa y la fecha de hoy.
- Los tests existentes de cada pantalla siguen pasando, abriendo el menú de la fila cuando
  corresponde. Ningún test se borra para que pase.
- Revisión visual con Gonza en el navegador, pantalla por pantalla, a 1440 px y a 1280 px.
- Definition of Done completa (backend sin cambios, se corre igual).

## Registro de gates

- Gate 1 (plan): aprobado por Gonza el 2026-10-28.
- Gate 2 (verificación): aprobado por Gonza el 2026-10-28, tras revisar en el navegador. Salida
  real: ruff y mypy sin errores, `makemigrations --check` sin cambios, pytest 769 pasados (96,89 %),
  frontend 345 tests (líneas 93,84 %, sentencias 91,45 %), lint, typecheck y build en verde,
  pre-commit (gitleaks incluido) sin hallazgos. Notas: Ingresos y Ocupación conservan scroll
  horizontal a 1280 px (una columna por mes; lo resuelve el selector de período de
  `pantallas-rediseno`), con la primera columna fija; Ítems a facturar y Posiciones por formato
  mantienen sus acciones en la fila porque abren campos en línea.
- Gate 3 (PR):
