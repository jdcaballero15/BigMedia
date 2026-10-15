# Recorrido: disponibilidad y reservas dentro de una campaña

15 de octubre de 2026 · Historias: HU-023, HU-028, HU-031, HU-032, HU-035, HU-037, HU-040 a HU-042, HU-055 a HU-059

Este documento describe cómo un operativo (Seba o Ale) consulta disponibilidad, selecciona carteles, detecta fechas superpuestas y crea o confirma reservas dentro de una campaña. Cubre carteles exclusivos y carteles con cupos.

**Alcance.** Recorrido, estados, mensajes y reglas de interfaz sobre las pantallas que ya definen las historias.

**Fuera de alcance.** Pantallas o documentos de cotización, pantallas nuevas que no estén en las historias, implementación en React y diseño visual definitivo (colores, tipografía).

Los nombres de marcas y direcciones de los ejemplos son ficticios.

## Conceptos que ve el operativo

### Dos tipos de cartel según su capacidad

La capacidad está en cada cartel, no en el formato (HU-011). La interfaz no muestra la palabra "capacidad": muestra lo que significa.

| Tipo | Cuándo | Cómo se muestra la disponibilidad | Ejemplo |
| --- | --- | --- | --- |
| **Exclusivo** | Capacidad 1. Gran Formato y la mayoría de los fijos | Libre u Ocupado | `Libre` · `Ocupado del 20/11 al 30/11` |
| **Con cupos** | Capacidad mayor a 1. LED (cupos del loop) y Séxtuples (slots) | Cupos libres sobre el total | `8 libres de 20` · `2 libres de 6` |

Un séxtuple es fijo pero tiene cupos (HU-009). La interfaz decide la forma de mostrarlo por la capacidad, no por la modalidad.

### Estados de la reserva y cómo se distinguen

| Estado | Bloquea en pantalla | Bloquea al confirmar otra | Cómo se dibuja |
| --- | --- | --- | --- |
| Pendiente | Sí (HU-028) | Según decisión [D-02](../decisiones/2026-10-15-pendientes-seba-ale.md#d-02-una-reserva-pendiente-bloquea-a-otras); hoy no | Rayado y etiqueta "Pendiente" |
| Confirmada | Sí | Sí | Relleno y etiqueta "Confirmada" |
| Finalizada | No (ya pasó) | No | Gris, solo en el histórico |
| Cancelada | No | No | Oculta por defecto; visible con el filtro "incluir canceladas" |

El estado siempre se escribe además del color o la trama, para no depender solo del color.

### Disponibilidad en un rango, no en un día

Cuando el operativo pregunta por un rango (por ejemplo, del 1/11 al 30/11), un cartel está **disponible** si tiene al menos un cupo libre **todos los días** del rango. Si solo algunos días están libres, el cartel está **parcialmente disponible** y la interfaz dice cuáles.

- Exclusivo: `Libre del 1/11 al 19/11 · Ocupado del 20/11 al 30/11`.
- Con cupos: `Mínimo 3 libres de 20 en el rango` o `Lleno del 15/11 al 18/11`.

Cómo se cuentan los cupos depende de la decisión [D-03](../decisiones/2026-10-15-pendientes-seba-ale.md#d-03-cómo-se-cuentan-los-cupos-dentro-de-un-rango): con conteo simple, "mínimo libres" es la capacidad menos las reservas que tocan el rango; con pico diario, es la capacidad menos el día más cargado. El texto de la interfaz es el mismo en los dos casos.

Si el día de borde es inclusivo (decisión [D-01](../decisiones/2026-10-15-pendientes-seba-ale.md#d-01-día-límite-entre-reservas-día-de-borde)), un rango que empieza el mismo día en que termina otra reserva se muestra como superpuesto en ese día.

## Mapa del recorrido

```
Consultar (opcional)          Armar la campaña                     Cerrar
─────────────────────         ──────────────────────────────       ─────────────────────────
Vista actual (HU-041)  ─┐     1. Crear campaña (HU-023)
Calendario  (HU-042)   ─┼──▶  2. Líneas de formato (HU-055)
                        │     3. Agregar carteles (HU-056)  ──▶    6. Completar campaña
                        │        └ detectar superposiciones          (cliente, marca, fechas)
                        │     4. Crear reservas Pendientes  ──▶    7. Confirmar campaña (HU-059)
                        │        en bloque (HU-057)                8. Confirmar reservas (HU-059)
                        │     5. Seguimiento (HU-058)                 └ resolver conflictos
                        │                                             (HU-032)
Ficha de reserva ───────┴──── Alternativa: una reserva suelta (HU-028, HU-031)
```

El camino principal es la campaña. La reserva suelta sigue existiendo para casos de un solo cartel o para corregir una reserva puntual.

## Paso 0 — Consultar disponibilidad sin armar nada

**Objetivo.** Responder "¿está libre en octubre?" sin abrir registros (HU-042).

**Desde dónde.** La vista actual (HU-041) o el calendario (HU-042). Si Seba responde que alcanza con la vista actual (decisión D-13), este paso usa solo HU-041.

**Recorrido.**

1. El operativo elige rango de fechas (por defecto 3 meses, ampliable a 12), zona, formato y modalidad.
2. La grilla muestra carteles en filas y semanas o meses en columnas.
   - En un exclusivo, la celda dice `Libre`, `Pendiente` u `Ocupado`.
   - En un cartel con cupos, la celda muestra lo usado sobre el total, por ejemplo `12/20`. Si en esa celda hay Pendientes, se indica aparte: `12/20 · 3 pendientes`.
3. Al hacer click en una celda ocupada se ven las reservas que la ocupan, con nombre de reserva, campaña, estado y fechas (HU-042, criterio 3).
4. Los carteles no operativos o de baja aparecen señalados o excluidos según el filtro (HU-042, criterio 4).

**Salida.** Esta vista es solo de consulta. Desde la celda se puede abrir la campaña de una reserva existente. No crea reservas ni campañas, para que el armado pase siempre por el paso 3.

## Paso 1 — Crear la campaña

Se puede guardar sin ningún dato (HU-023). Si el operativo ya sabe la marca y las fechas planificadas, conviene cargarlas ahora: las fechas se usan después como valor por defecto en "Agregar carteles".

La ficha de campaña muestra desde el principio:

- Estado (Cotizada, Confirmada, Cancelada, Perdida).
- Cliente que factura, deducido de la marca.
- Líneas de formato con solicitado, reservado y faltante (HU-058).
- Lista de reservas con su estado.
- Monto total y cantidad de reservas, de solo lectura (HU-025).
- Acciones: "Agregar carteles", "Confirmar campaña" y "Confirmar reservas".

## Paso 2 — Indicar cuántas posiciones se necesitan

El operativo agrega líneas de formato con cantidad, por ejemplo "Gran Formato · 100" y "Séxtuples · 40" (HU-055).

- La cantidad es opcional.
- No se puede repetir un formato. Si lo intenta: *"Esta campaña ya tiene una línea de Séxtuples. Cambiá su cantidad en lugar de agregar otra."*

En una línea de un formato con cupos, la cantidad cuenta **posiciones**, es decir, reservas: un cupo de LED o un slot de séxtuple. Si una marca puede comprar más de un cupo en el mismo cartel (decisiones [D-04](../decisiones/2026-10-15-pendientes-seba-ale.md#d-04-cupos-de-los-led) y [D-05](../decisiones/2026-10-15-pendientes-seba-ale.md#d-05-slots-de-los-séxtuples)), hay que revisar esta definición.

## Paso 3 — Agregar carteles y detectar superposiciones

Es la pantalla "Agregar carteles" de HU-056.

### 3.1 Entrada

- La campaña viene precargada y no se puede cambiar.
- El operativo elige una línea de formato.
- Las fechas de la tanda vienen de la campaña. Si la campaña no tiene fechas, la pantalla las pide y no deja avanzar sin ellas (HU-056, criterio 2). Siempre se pueden ajustar para esta tanda.

### 3.2 Lista de carteles

Filtros: zona, proveedor y dirección parcial, sin distinguir mayúsculas ni tildes.

Cada fila muestra:

- Nombre legible: Dirección + Tamaño, o Dirección + Slots en séxtuples. Nunca un código interno.
- Zona y proveedor.
- Disponibilidad en el rango, según el tipo de cartel.
- Tarifa de lista, para el monto estimado.
- Avisos de superposición, si los hay (ver 3.3).

Por defecto la lista muestra solo carteles **disponibles en todo el rango** (HU-056, criterio 1). Un interruptor "Mostrar no disponibles" agrega los parcialmente disponibles y los llenos, deshabilitados y con el motivo. Así el operativo entiende por qué falta un cartel que esperaba ver, sin poder seleccionarlo.

```
Agregar carteles · Campaña: Marca Ejemplo Primavera
Línea: Gran Formato (solicitadas 100)   Fechas: 01/11/2026 – 30/11/2026  [cambiar]
Zona [Todas ▾]  Proveedor [Todos ▾]  Dirección [            ]  [ ] Mostrar no disponibles

[x] Seleccionar todos los filtrados (57)
[x] Av. Ejemplo 123 · 6x3          Zona A   Libre
[x] Calle Ficticia 456 · 8x4       Zona B   Libre · 1 pendiente de otra campaña  ⚠
[ ] Ruta Inventada km 3 · 6x3      Zona A   Ya está en esta campaña (01/11 – 15/11)  ⚠
──────────────────────────────────────────────────────────────────────────────
Seleccionados: Gran Formato 60 de 100 · Monto estimado: $ …
                                                     [Crear reservas pendientes]
```

Para un formato con cupos, la columna de disponibilidad cambia:

```
Línea: Séxtuples (solicitadas 40)   Fechas: 01/11/2026 – 30/11/2026
[x] Calle Ficticia 789 · 6 slots    Zona C   Mínimo 2 libres de 6
[x] Pasaje Ejemplo 10 · 4 slots     Zona C   1 libre de 4 · 2 pendientes de otras campañas  ⚠
```

### 3.3 Superposiciones que se avisan al seleccionar

En este paso el sistema **avisa, no bloquea**. Los avisos ayudan a elegir. El bloqueo real ocurre al confirmar, en el servidor (paso 8).

| Situación | Exclusivo | Con cupos | Qué hace la interfaz |
| --- | --- | --- | --- |
| Libre todo el rango | `Libre` | `N libres de M` | Seleccionable, sin aviso |
| Hay Pendientes de otras campañas en el rango | `Libre · 1 pendiente de otra campaña` | `N libres de M · K pendientes de otras campañas` | Seleccionable con aviso. Al pasar el mouse o tocar el aviso, muestra campaña y fechas de cada Pendiente |
| Las Pendientes llenarían el cartel | Libre solo si no se cuentan las Pendientes | Libre solo si no se cuentan las Pendientes | Con D-02 = solo visual: seleccionable con aviso fuerte *"Si la otra campaña confirma antes, esta reserva quedará en conflicto"*. Con D-02 = bloqueo duro: no disponible |
| Ocupado algunos días del rango | `Libre del 1/11 al 19/11` | `Lleno del 15/11 al 18/11` | No disponible para esta tanda. Visible con "Mostrar no disponibles", con los días libres. Para usarlo, el operativo crea otra tanda con esas fechas |
| Ocupado o lleno todo el rango | `Ocupado` | `Lleno` | No disponible. Visible con "Mostrar no disponibles", con la reserva que lo ocupa |
| El cartel ya tiene una reserva de esta misma campaña que se superpone | `Ya está en esta campaña (fechas)` | Igual | Deseleccionado por defecto. Si se selecciona, pide confirmar: *"Esta campaña ya reserva este cartel del 01/11 al 15/11. ¿Agregar otra reserva?"* |
| Cartel no operativo (HU-039) o de baja | — | — | No se lista. Con "Mostrar no disponibles" aparece con su estado |

### 3.4 Selección y contador

- "Seleccionar todos los filtrados" selecciona solo los disponibles visibles. Después se pueden destildar excepciones (HU-056, criterio 4).
- El contador muestra el avance de la línea (`Gran Formato 60 de 100`) y el monto estimado con la tarifa de lista. Si la línea no tiene cantidad, muestra solo lo seleccionado.
- Si la selección supera o no alcanza lo solicitado, al crear aparece un aviso que deja continuar (HU-056, criterio 6): *"Seleccionaste 60 de las 100 posiciones de Gran Formato. Podés agregar más después."*

### 3.5 La lista puede quedar desactualizada

Mientras el operativo arma la selección, otra persona puede confirmar reservas sobre los mismos carteles. La lista es una foto del momento: el servidor vuelve a validar al crear (paso 4) y al confirmar (paso 8). Si la lista tiene más de unos minutos, la pantalla ofrece "Actualizar disponibilidad" sin perder la selección. Los carteles que dejaron de estar disponibles quedan marcados.

## Paso 4 — Crear las reservas Pendientes en bloque

Al pulsar "Crear reservas pendientes" se crea una reserva por cada cartel seleccionado (HU-057):

- Estado Pendiente.
- Fechas de la tanda.
- Precio de alquiler tomado de la tarifa de lista, editable después.
- Nombre automático "Marca - Cartel - Mes", o "Sin marca" si la campaña todavía no tiene marca.

**Durante.** Una barra de progreso muestra `120 de 200 creadas`. El operativo puede salir de la pantalla: la operación sigue en el servidor.

**Al terminar.** Un resumen indica cuántas se crearon y cuáles fallaron, con el motivo de cada una:

```
Se crearon 198 reservas pendientes.
No se pudieron crear 2:
  · Calle Ficticia 456 · 8x4 — El cartel pasó a "En mantenimiento" mientras armabas la selección.
  · Av. Ejemplo 123 · 6x3   — Ya existe una reserva de esta campaña para este cartel en estas fechas.
[Reintentar las fallidas]  [Volver a la campaña]
```

"Reintentar las fallidas" solo procesa esas. Las ya creadas no se duplican (HU-057, criterios 4 y 5).

Crear una reserva Pendiente no valida el cupo de forma dura (HU-031). Por eso este paso puede crear Pendientes sobre carteles que se llenaron mientras tanto. El conflicto aparece al confirmar.

## Paso 5 — Seguimiento de lo que falta

La ficha de campaña muestra por línea (HU-058):

```
Formato         Solicitadas  Reservadas  Faltan   Pendientes  Confirmadas
Gran Formato        100           60        40          60           0
Séxtuples            40           40         0          38           2
```

- Las Canceladas no cuentan como reservadas.
- Si cambian las fechas de la campaña y hay Pendientes, el sistema pregunta si actualizarlas. Las Confirmadas no se tocan desde acá.

## Paso 6 — Completar la campaña

Antes de confirmar hay que cargar cliente que factura, marca y fechas (propuesta de HU-059, decisión [D-11](../decisiones/2026-10-15-pendientes-seba-ale.md#d-11-se-puede-confirmar-una-campaña-incompleta)). La ficha muestra qué falta antes de que el operativo lo intente:

*"Para confirmar la campaña falta: marca."*

Al cargar la marca, los nombres de las reservas "Sin marca" se corrigen solos (HU-030).

## Paso 7 — Confirmar la campaña

"Confirmar campaña" cambia el estado de la campaña a Confirmada. No confirma reservas: es un compromiso comercial.

Si falta un dato, se rechaza con la lista de lo que falta (HU-059, criterio 1).

## Paso 8 — Confirmar las reservas y resolver conflictos

"Confirmar reservas" envía todas las Pendientes de la campaña al servidor. El servidor valida cada cartel de forma atómica (HU-031, HU-034):

- Las que tienen cupo pasan a Confirmada.
- Las que no tienen cupo quedan Pendientes, con su conflicto.

No es todo o nada: un conflicto no frena a las demás (HU-059).

### Resultado

```
Se confirmaron 190 reservas.
10 quedaron pendientes por falta de cupo:

Cartel                         Cupos       Fechas en conflicto     Ocupado por
Calle Ficticia 456 · 8x4       1 de 1      20/11 – 30/11           Marca Otra - Calle Ficticia 456 8x4 - Nov 2026
                                                                   (Campaña Otra Navidad · Confirmada)
Pasaje Ejemplo 10 · 4 slots    4 de 4      15/11 – 18/11           4 reservas [ver]
…
[Volver a confirmar las pendientes]
```

Cada conflicto nombra el cartel, los cupos ocupados sobre la capacidad, las fechas y las reservas que chocan (HU-032). No usa códigos ni términos técnicos.

### Qué puede hacer el operativo con cada conflicto

Desde la fila del conflicto:

| Acción | Qué hace | Cuándo conviene |
| --- | --- | --- |
| **Cambiar fechas** | Abre la reserva para editar sus fechas. Muestra los días libres del cartel | El cartel está libre en otro período aceptable para el cliente |
| **Reemplazar por otro cartel** | Cancela esta Pendiente y abre "Agregar carteles" con la misma línea, las mismas fechas y la zona del cartel original como filtro | El cliente acepta otra ubicación |
| **Cancelar** | Pasa la reserva a Cancelada. Pide confirmación | La posición ya no hace falta |
| **Dejar pendiente** | No hace nada | Se espera que la otra campaña libere el cartel |
| **Ver la reserva que ocupa** | Abre la reserva y la campaña en conflicto | Para saber a quién llamar |

"Volver a confirmar las pendientes" procesa solo las que siguen Pendientes (HU-059, criterio 5).

### Dos campañas confirman a la vez

Si otra persona confirma el último cupo un instante antes, el resultado lo explica igual que cualquier conflicto, con la campaña que se quedó el cupo (HU-059, criterio 4). La interfaz no sugiere "intentar de nuevo" porque el resultado sería el mismo.

## Alternativa — Una reserva suelta

Desde la ficha de campaña, "Agregar reserva" abre el formulario de HU-028 con la campaña seleccionada.

1. El operativo elige el cartel con un buscador por dirección. Junto a cada resultado se ve la disponibilidad en las fechas cargadas, con las mismas etiquetas del paso 3.
2. Carga fecha de inicio y de fin. Son obligatorias y la de fin no puede ser anterior a la de inicio.
   - Error: *"La fecha de fin no puede ser anterior a la de inicio."*
3. Al elegir cartel y fechas, el formulario muestra la superposición antes de guardar: *"En estas fechas el cartel tiene 1 reserva pendiente de otra campaña."*
4. El precio de alquiler se precarga desde la tarifa de lista. Impresión y fijación se cargan a mano. El total se calcula solo.
5. Botones: "Guardar como pendiente" y "Guardar y confirmar". El segundo valida en el servidor; si no hay cupo, muestra el mismo mensaje de conflicto que el paso 8 y la reserva no se guarda como Confirmada.

### Editar una reserva Confirmada

- Si cambian solo precios, se guarda sin revalidar (HU-031, criterio 5).
- Si cambian las fechas, el cartel o el estado, se revalida. Ante un conflicto, la reserva conserva los valores anteriores y se muestra el mensaje:

*"No se pudieron cambiar las fechas. Calle Ficticia 456 · 8x4 tiene 1 de 1 cupos ocupados del 20/11 al 30/11 por Marca Otra - Calle Ficticia 456 8x4 - Nov 2026. La reserva sigue del 01/11 al 15/11."*

### Cancelar

Cancelar siempre se permite y libera el cupo (HU-037). Pide una confirmación simple que dice qué se libera:

*"¿Cancelar Marca Ejemplo - Av. Ejemplo 123 6x3 - Nov 2026? El cartel quedará libre del 01/11 al 30/11."*

Las reglas que faltan (motivo, cancelar la campaña entera, reservas en curso) dependen de la decisión [D-06](../decisiones/2026-10-15-pendientes-seba-ale.md#d-06-reglas-de-cancelación).

## Reglas de interfaz

1. **El servidor decide.** La interfaz avisa y ayuda a elegir, pero nunca da por confirmada una reserva sin la respuesta del servidor.
2. **Siempre el nombre legible.** Carteles por Dirección + Tamaño o Slots; reservas por su nombre automático.
3. **Exclusivo y con cupos usan el mismo lugar en pantalla.** Cambia solo el texto de disponibilidad (`Libre` contra `N libres de M`).
4. **Avisar no es bloquear.** Pendientes ajenas, cantidades distintas de lo solicitado y reservas repetidas en la misma campaña generan avisos. Solo bloquean la falta de cupo al confirmar, los datos obligatorios y los carteles no operativos.
5. **Sin depender del color.** Cada estado lleva texto. Las celdas del calendario llevan número o palabra.
6. **Mensajes con datos.** Todo conflicto dice cartel, cupos, fechas y quién ocupa. Ningún mensaje es genérico.
7. **Teclado.** La lista de selección se puede recorrer y tildar con teclado, porque se usa con cientos de filas.

## Decisiones que cambian este recorrido

| Decisión | Qué cambia |
| --- | --- |
| [D-01 Día de borde](../decisiones/2026-10-15-pendientes-seba-ale.md#d-01-día-límite-entre-reservas-día-de-borde) | Si el día compartido aparece como superposición en los avisos y en el calendario |
| [D-02 Pendiente](../decisiones/2026-10-15-pendientes-seba-ale.md#d-02-una-reserva-pendiente-bloquea-a-otras) | Si un cartel con Pendientes ajenas es seleccionable con aviso o no disponible |
| [D-03 Conteo de cupos](../decisiones/2026-10-15-pendientes-seba-ale.md#d-03-cómo-se-cuentan-los-cupos-dentro-de-un-rango) | El número "mínimo libres" en carteles con cupos |
| [D-04 LED](../decisiones/2026-10-15-pendientes-seba-ale.md#d-04-cupos-de-los-led) y [D-05 Séxtuples](../decisiones/2026-10-15-pendientes-seba-ale.md#d-05-slots-de-los-séxtuples) | Si una reserva puede ocupar varios cupos o un slot concreto. Haría falta elegir cantidad o posición en el paso 3 |
| [D-06 Cancelación](../decisiones/2026-10-15-pendientes-seba-ale.md#d-06-reglas-de-cancelación) | Confirmación de cancelación, motivo y efecto de cancelar la campaña |
| [D-11 Campaña incompleta](../decisiones/2026-10-15-pendientes-seba-ale.md#d-11-se-puede-confirmar-una-campaña-incompleta) | Si el paso 6 es obligatorio antes del 7 |
| [D-13 Vista a futuro](../decisiones/2026-10-15-pendientes-seba-ale.md#d-13-vista-de-disponibilidad-a-futuro-pregunta-20) | Si el paso 0 usa el calendario o solo la vista actual |

## Preguntas de UX para la demo con Seba y Ale

1. ¿Arman las campañas por formato y cantidad (como propone HU-055) o eligen cartel por cartel?
2. Cuando un cartel está libre solo parte del mes, ¿lo ofrecen igual al cliente con fechas distintas? Eso define si conviene permitir fechas por cartel dentro de una misma tanda.
3. ¿El interruptor "Mostrar no disponibles" les sirve o prefieren no verlos nunca?
4. Ante un conflicto, ¿qué hacen más seguido: cambiar fechas, cambiar de cartel o esperar?
