# Unidad: Ajuste de espaciado del detalle de campaña

- **Estado:** en curso · **Épica:** E12 Rediseño visual · **App dueña:** `frontend`
- **Origen:** pedido de Juan Diego (2026-11-08), al probar HU-069 en staging · **Rama:** `fix/frontend-espaciado-detalle-campania`

## Objetivo

El detalle de campaña se ve apretado y desproporcionado: el texto queda pegado al borde de las
tarjetas, las tarjetas se tocan entre sí y el botón "Agregar línea" ocupa una columna entera. Se
corrige el espaciado de esa pantalla, sin cambiar qué muestra ni cómo funciona.

## Causa

La tarjeta (`.card` en `App.css`) no tiene espacio interior a propósito: así las tablas llegan de
borde a borde. Cada parte de adentro trae su propio espacio (`.card-heading`, `.filters`,
`.edit-form`). En el detalle de campaña hay tres partes que no lo traen:

1. La tarjeta de datos (Estado, Marca, Cliente que factura, Período): `detail-grid` sin espacio
   interior ni separación con la tarjeta de abajo.
2. El alta de línea de "Posiciones por formato": `form-grid` sin espacio interior, con el botón como
   tercera columna de la grilla, que lo estira a todo el ancho y alto de la columna.
3. La sección nueva "Órdenes de publicidad" (HU-069): la lista y los avisos sin espacio interior.

## Cambios

- `App.css`:
  - Clase nueva `.card-cuerpo` (espacio interior de 1rem a 1.2rem, alineado con `.card-heading`)
    para el contenido de una tarjeta que no es una tabla.
  - En un `form-grid`, el botón de enviar queda abajo y a la izquierda con su ancho natural, en
    lugar de estirarse (`align-self: end; justify-self: start`).
- `CampaniaDetalle.tsx`: la tarjeta de datos lleva `card-cuerpo` y `section-gap`.
- `PosicionesPorFormato.tsx`: el alta de línea lleva `card-cuerpo`.
- `OrdenesPublicidad.tsx`: encabezado con `card-heading`, contenido con `card-cuerpo` y separación
  con `section-gap`, como las demás secciones del detalle.

## Fuera de alcance

- Las demás pantallas: se revisan a simple vista en staging, pero no se cambian salvo que el botón
  del `form-grid` se vea mal en alguna. En ese caso se anota y se decide aparte.
- El nombre de la sección del menú lateral ("Ingresos") que aparece al pasar el mouse y puede
  tapar contenido: es el comportamiento del menú desplegable de la unidad anterior y no forma
  parte de este pedido.

## Migraciones

Ninguna.

## Reglas provisorias que se usan

Ninguna.

## Cómo se prueba

- Los tests actuales de `CampaniaDetalle`, `PosicionesPorFormato` y `OrdenesPublicidad` siguen
  pasando: el cambio es de clases y estilos, no de comportamiento.
- Test nuevo: la tarjeta de datos y el alta de línea llevan `card-cuerpo`, para que el espaciado no
  se pierda en un cambio futuro.
- Verificación completa del frontend (`format:check`, `lint`, `typecheck`, `test:coverage`, `build`).
- Prueba visual en staging: el detalle de una campaña con posiciones y órdenes de publicidad, en
  pantalla ancha y angosta.

## Registro de gates

- Gate 1 (plan): pendiente
- Gate 2 (verificación): pendiente
- Gate 3 (PR): pendiente
