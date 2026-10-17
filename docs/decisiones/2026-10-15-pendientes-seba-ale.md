# Decisiones pendientes para consultar con Seba y Ale

15 de octubre de 2026 · Fuente: [historias de usuario](../requisitos/historias-de-usuario.md)

Este documento ordena por prioridad las decisiones de negocio que todavía no están cerradas en las historias de usuario. Para cada una indica qué parte del sistema queda bloqueada, qué default se usa mientras tanto y dónde anotar la respuesta.

Las historias citan "preguntas" numeradas (por ejemplo, "pregunta 10"). Esa lista numerada no está en el repositorio; acá se las nombra por tema y se conserva el número entre paréntesis cuando la historia lo menciona.

## Cómo se priorizó

- **P1 — Bloquea el núcleo.** Sin la respuesta no se puede cerrar el motor de disponibilidad (épica E5), el modelo de datos del cartel o la reserva, ni sus pruebas automáticas. Un cambio posterior obliga a migrar datos o reescribir la validación.
- **P2 — Bloquea una historia Must o la carga inicial.** Hay un default razonable, pero condiciona la importación del inventario o un flujo central de campañas.
- **P3 — Ajusta detalles.** Afecta historias Should o Could, o se puede cambiar después por configuración sin costo alto.

## Resumen

| Nº | Decisión | Prioridad | Responde | Bloquea | Default mientras tanto |
| --- | --- | --- | --- | --- | --- |
| D-01 | Día límite entre reservas (día de borde) | P1 | Seba y Ale | Validación de solapamiento, pruebas, calendario | Inclusivo: el día compartido se pisa |
| D-02 | ¿Una reserva Pendiente bloquea a otras? | P1 | Seba y Ale | Validación, selección de carteles, confirmación en bloque | Ocupa cupo solo visualmente; bloqueo duro al confirmar |
| D-03 | Cómo se cuentan los cupos dentro de un rango | P1 | Seba y Ale | Validación en carteles con cupos, ocupación | Se cuentan todas las reservas que tocan el rango |
| D-04 | Cupos de los LED | P1 | Seba y Ale | Modelo de cartel y reserva, validación, reportes | Capacidad editable por cartel; una reserva = un cupo |
| D-05 | Slots de los séxtuples | P1 | Seba y Ale | Identidad del cartel, importación, validación | Capacidad = slots relevados; una reserva = un slot genérico |
| D-06 | Reglas de cancelación | P1 | Seba y Ale | Ciclo de vida de reserva y campaña, reportes de ingresos | Cancelar siempre se permite y libera el cupo |
| D-07 | Propiedad de los carteles | P1 | Gonzalo y Diego, con datos de Seba y Ale | Modelo de cartel, costos, rentabilidad, importación | Costos solo de impresión y fijación |
| D-08 | Lista de zonas (departamentos) | P2 | Seba y Ale | Importación del inventario, alta de carteles | Lista vacía y administrable |
| D-09 | Contenido real de los relevamientos | P2 | Seba y Ale | Importación del inventario | Sin carga hasta tener los archivos |
| D-10 | Estados físicos y reservas de carteles fuera de servicio | P2 | Seba y Ale | Estados del cartel, alertas, bloqueo de reservas | Alertar y bloquear reservas nuevas |
| D-11 | ¿Se puede confirmar una campaña incompleta? | P2 | Seba y Ale | Confirmación de campaña, reportes | Se exigen cliente, marca y fechas |
| D-12 | Reservas con fechas pasadas | P2 | Seba y Ale | Importación histórica, alta manual | No se permite a mano; histórico solo por importación |
| D-13 | ¿Hace falta la vista de disponibilidad a futuro? | P3 | Seba y Ale | Calendario de disponibilidad | Se construye como Should |
| D-14 | Cambio de pagador de una marca | P3 | Seba y Ale | Cliente que factura de la campaña | Se deduce siempre de la marca |
| D-15 | Intermediario formal y sus contactos | P3 | Seba y Ale | Clientes y contactos | Tipo aparte con contactos múltiples |
| D-16 | Otras preguntas menores | P3 | Seba y Ale | Ver detalle | Ver detalle |

Las preguntas que corresponden a Administración (facturación) están al final, en un bloque aparte.

---

## P1 — Bloquean el núcleo

### D-01 Día límite entre reservas (día de borde)

**Pregunta.** Si una reserva termina el 15 y la siguiente empieza el 15 en el mismo cartel, ¿chocan o no?

**Para entender mejor la respuesta, preguntar también:**

1. ¿La fecha de fin es el último día que el aviso está a la vista, o el día en que se retira?
2. ¿Ese día se saca la lona anterior y se coloca la nueva? ¿A cuál de las dos campañas pertenece el día de cambio?
3. ¿Los alquileres suelen empezar el 1 y el 16, o en cualquier día? (HU-051 menciona alquileres mensuales y de 15 días.)
4. ¿La regla es igual para LED, donde no hay cambio físico de lona?

**Opciones.**

- **Inclusivo:** el 15 se pisa. Dos reservas seguidas deben ser, por ejemplo, 1–15 y 16–30.
- **Exclusivo:** el 15 no se pisa. Se puede reservar 1–15 y 15–30.
- **Distinto por modalidad:** inclusivo para fijos y exclusivo para digitales, o al revés. Esta opción no está prevista en las historias y agregaría un parámetro.

**Default.** Inclusivo (HU-001).

**Bloquea.**

- Validación de solapamiento al confirmar (HU-031) y caso 6 de la matriz de pruebas.
- Parámetro configurable (HU-001, HU-033).
- Cálculo de ocupación hoy y en el calendario (HU-040, HU-042).
- Reparto de ingresos por día (HU-051): define si el día de borde se cuenta en una o en dos reservas.

Aunque sea configurable, la respuesta define el valor inicial con el que se cargan los datos reales. Cambiarlo después puede hacer aparecer conflictos en reservas ya confirmadas.

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

### D-02 ¿Una reserva Pendiente bloquea a otras?

**Pregunta.** Si dos campañas cotizan el mismo cartel en las mismas fechas, ¿la primera que lo cargó lo tiene asegurado o gana la primera que confirma?

**Ejemplo para la reunión.** La campaña A carga el cartel X para noviembre como Pendiente el lunes. El miércoles la campaña B quiere el mismo cartel y la misma fecha, y confirma enseguida. ¿Se le permite a B?

**Opciones.**

- **A. Solo visual (default actual).** La Pendiente se muestra como ocupación, pero no impide confirmar a otra campaña. Gana quien confirma primero. A queda Pendiente con conflicto.
- **B. Bloqueo duro.** La Pendiente cuenta para el bloqueo. B no puede confirmar. Riesgo: carteles retenidos por cotizaciones que nunca cierran.
- **C. Bloqueo con vencimiento.** La Pendiente bloquea durante N días y después pasa a solo visual. No existe en las historias: requiere una historia nueva y una tarea programada.

**Bloquea.**

- Validación dura (HU-031) y parámetro "la tentativa ocupa cupo" (HU-001, HU-033), caso 9 de la matriz.
- La lista de "Agregar carteles" (HU-056): define si un cartel con Pendientes de otra campaña aparece como libre.
- Confirmación en bloque (HU-059): define qué campaña se queda el cupo.
- Calendario y vista actual (HU-041, HU-042): cómo se dibuja una Pendiente.

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

### D-03 Cómo se cuentan los cupos dentro de un rango

Esta pregunta surge de leer HU-031 y no figura como pendiente en las historias. Solo importa en carteles con más de un cupo (LED y séxtuples).

**Pregunta.** En un LED de 20 cupos, una reserva ocupa del 1 al 10 de noviembre y otra del 20 al 30. Nunca están al aire juntas. ¿Para una reserva nueva del 1 al 30 hay 19 cupos libres o 18?

**Opciones.**

- **Conteo simple (lo que dice hoy HU-031).** Cuenta todas las reservas que tocan el rango: 18 libres. Es más fácil de explicar, pero subestima la disponibilidad y puede rechazar reservas que en realidad entran.
- **Pico diario.** Calcula, día por día, cuántos cupos están ocupados y usa el día más cargado: 19 libres. Es exacto, pero el mensaje de conflicto tiene que indicar qué días están llenos.

**Bloquea.**

- Fórmula de la validación de solapamiento (HU-031) y prueba de concurrencia con capacidad 20 (HU-034).
- Contador "12 de 20" en ocupación y calendario (HU-040, HU-042).
- Lista de carteles "con cupo libre en el rango" (HU-056).
- Mensaje de conflicto (HU-032).

Con capacidad 1 las dos opciones dan el mismo resultado, así que no afecta a los carteles exclusivos.

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

### D-04 Cupos de los LED

**Preguntas.**

1. ¿Qué es un cupo en un LED? ¿Un spot de cierta duración dentro de un loop? ¿Cuántos segundos dura el loop?
2. ¿Todos los LED tienen la misma cantidad de cupos? (Las historias lo dejan abierto como "capacidad uniforme de los LED".)
3. ¿Una marca puede comprar más de un cupo en el mismo LED y el mismo período (por ejemplo, doble frecuencia)?
4. ¿La capacidad de un LED cambia con el tiempo (por ejemplo, se agranda el loop)?
5. ¿Los LED se venden por día, por semana, por quincena o por mes?

**Por qué importa.** Las historias suponen que una reserva ocupa exactamente un cupo. Si una marca puede comprar dos o más, hay dos caminos: agregar una "cantidad de cupos" a la reserva o crear varias reservas iguales. Las dos cambian el modelo de datos, la validación y la creación en bloque.

**Default.** La capacidad se precarga desde el formato y se edita por cartel (HU-011). Cada reserva ocupa un cupo.

**Bloquea.**

- Modelo de cartel y de reserva (HU-011, HU-028).
- Validación y concurrencia (HU-031, HU-034).
- Creación en bloque, que hoy crea una reserva por posición (HU-057).
- Ocupación en días-cupo (HU-040, HU-048).
- Una futura plantilla de importación de LED, que hoy no tiene relevamiento.

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

### D-05 Slots de los séxtuples

**Preguntas.**

1. Cuando una marca compra un séxtuple, ¿compra un slot cualquiera o un slot concreto (por ejemplo, "el de arriba a la izquierda")?
2. ¿Una marca puede ocupar más de un slot del mismo séxtuple a la vez?
3. Si se rompe un slot, ¿baja la capacidad del cartel o se marca el slot como fuera de servicio?
4. Big Media identifica un séxtuple por Dirección + cantidad de slots (HU-010). Si el séxtuple cambia de 6 a 4 slots, ¿es el mismo cartel? ¿Puede haber dos séxtuples en la misma dirección?
5. ¿Hay alguna restricción entre marcas que comparten un séxtuple, por ejemplo competidores directos? (No figura en las historias; preguntarlo solo para descartarlo.)

**Por qué importa.** Si el cliente elige un slot concreto, la reserva necesita guardar qué slot ocupa y la validación pasa de "hay cupo" a "este slot está libre". Además, si la cantidad de slots es parte de la identidad del cartel, cambiarla puede crear un duplicado en la importación.

**Default.** La capacidad es igual a los slots relevados (HU-015) y cada reserva ocupa un slot genérico, sin posición.

**Bloquea.**

- Clave para detectar duplicados en la importación de los 226 séxtuples (HU-015, ver [importación](../importacion/README.md)).
- Nombre legible del cartel (HU-010) y de la reserva (HU-030).
- Reducción de capacidad con reservas a futuro (HU-011).
- Validación (HU-031) y creación en bloque (HU-057).

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

### D-06 Reglas de cancelación

Hoy las historias dicen que cancelar siempre se permite, no borra y libera el cupo (HU-037). Faltan varias reglas que cambian datos y reportes.

**Preguntas.**

1. **Cancelada o perdida (pregunta 6).** ¿Usan las dos palabras para cosas distintas? Propuesta actual: "perdida" es una cotización que nunca cerró y "cancelada" es una confirmada que se cayó y quizás facturó seña.
2. **Cancelar la campaña.** Al cancelar una campaña confirmada, ¿se cancelan solas todas sus reservas? Las historias no lo dicen.
3. **Cancelación con la exhibición en curso.** Si una reserva del 1 al 30 se cae el día 10, ¿se cancela entera o se acorta la fecha de fin al 10? Lo primero borra 10 días ya exhibidos de los reportes de ingresos y ocupación.
4. **Reprogramar (pregunta 10).** Cuando un cliente corre las fechas, ¿se editan las fechas de la misma reserva o se cancela y se crea otra?
5. **Seña.** ¿Una cancelación puede generar algo a facturar (seña o penalidad)? ¿Quién lo carga?
6. **Motivo.** ¿Quieren registrar un motivo al cancelar (cliente desistió, cartel roto, error de carga)? No está en las historias, pero serviría para los reportes.
7. **Permisos.** ¿Cualquier operativo puede cancelar una reserva confirmada, o solo quien la cargó o el administrador?
8. **Reactivar.** ¿Necesitan volver a confirmar una reserva cancelada (HU-035 lo permite revalidando el cupo) o prefieren crear una nueva?

**Default.** Cancelar siempre se permite, cancela la reserva entera, libera el cupo de inmediato y no pide motivo. La campaña distingue cancelada de perdida.

**Bloquea.**

- Estados y transiciones de campaña y de reserva (HU-024, HU-035, HU-037).
- Reparto de ingresos por día y margen de campaña (HU-045, HU-051), si se acortan las reservas en curso.
- Seguimiento de solicitado, reservado y faltante (HU-058).
- Vínculo con los ítems a facturar (HU-060), si una cancelación genera seña.

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

### D-07 Propiedad de los carteles

Según las historias, esta pregunta la responden Gonzalo y Diego. Seba y Ale pueden adelantar el dato práctico: qué carteles son de terceros.

**Preguntas.**

1. ¿Big Media es dueña de todos los carteles, revende espacio de terceros o tiene de los dos tipos?
2. Si es mixto, ¿los relevamientos de Gran Formato y Séxtuples indican cuáles son de terceros y de qué proveedor?
3. En los carteles de terceros, ¿Big Media paga un alquiler fijo, un porcentaje o algo por campaña?

**Por qué importa.** Define si el cartel necesita un campo "tipo de propiedad" y una tarifa de costo, si el proveedor es obligatorio y si el módulo de costos lleva cerca de 20 o 60 horas (HU-046).

**Default.** Solo se registran costos de impresión y fijación. El alquiler no se carga como costo.

**Bloquea.**

- Modelo de cartel y columnas de la plantilla de importación (HU-010, HU-015).
- Costos y rentabilidad (HU-043, HU-044, HU-046), y reporte de margen por proveedor.

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

---

## P2 — Bloquean una historia Must o la carga inicial

### D-08 Lista de zonas (departamentos)

**Pregunta.** ¿Cuáles son los 9 departamentos de Mendoza en los que hay carteles, escritos exactamente como los usan? ¿Hace falta una zona más fina, como un barrio o un corredor?

**Bloquea.** La zona es obligatoria en el cartel (HU-010), así que sin esta lista no se puede importar ningún cartel (HU-015). También afecta los filtros del inventario y de los reportes (HU-013, HU-014, HU-048).

**Default.** Lista vacía y administrable.

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

### D-09 Contenido real de los relevamientos

**Preguntas.**

1. ¿Pueden compartir las planillas de Gran Formato (66 o más posiciones) y de Séxtuples (226 posiciones) tal como están hoy?
2. En Gran Formato, ¿el tamaño se escribe siempre como ancho × alto en metros (por ejemplo "6x3")?
3. ¿Los colores o celdas combinadas de la planilla significan algo (estado, cliente actual, proveedor)?
4. ¿Las planillas tienen tarifa de lista, proveedor o foto, o eso se completa después?
5. ¿Hay carteles que figuran dos veces a propósito, por ejemplo dos caras en la misma dirección?

**Bloquea.** La transformación a la [plantilla CSV](../importacion/README.md) y las reglas de duplicados (HU-015).

**Default.** No se carga nada hasta tener los archivos. No se inventan datos.

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

### D-10 Estados físicos y carteles fuera de servicio (preguntas 9 y 18)

**Preguntas.**

1. Además de Activo, En mantenimiento, De baja, Apagado y Vidrio destruido, ¿hay otros estados?
2. Si un cartel con reservas confirmadas se rompe, ¿qué hacen hoy? ¿Reubican a la marca en otro cartel, acortan la reserva o la cancelan?
3. ¿Un cartel en mantenimiento puede recibir reservas para fechas futuras, cuando ya esté reparado?

**Default.** Se alerta, se listan las reservas afectadas sin modificarlas y se bloquean las reservas nuevas mientras el cartel no esté operativo.

**Bloquea.** Estados del cartel (HU-012), alertas (HU-039), caso 16 de la matriz de pruebas y la columna `estado` de la importación.

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

### D-11 ¿Se puede confirmar una campaña incompleta?

**Pregunta.** ¿Alguna vez confirman una campaña sin saber todavía la marca o quién factura?

**Default.** Para confirmar se exigen cliente que factura, marca y fechas (HU-059). Si Seba prefiere permitirlo, se quita la exigencia y los reportes muestran un grupo "(vacío)".

**Bloquea.** Confirmación de campaña (HU-024, HU-059), nombre de las reservas "Sin marca" (HU-030) y reportes por cliente y marca (HU-049).

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

### D-12 Reservas con fechas pasadas (preguntas 8 y 11)

**Preguntas.**

1. ¿Existe un histórico de reservas? ¿En qué formato, de cuántos años y con qué calidad?
2. ¿Un operativo necesita cargar a mano una reserva que ya ocurrió, por ejemplo una que se olvidó registrar?

**Default.** Las históricas entran como Finalizadas solo por importación (HU-038). La carga manual con fecha pasada no se permite.

**Bloquea.** Importación histórica (HU-038) y reportes con comparativo interanual (HU-048, HU-049).

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

---

## P3 — Ajustan detalles

### D-13 Vista de disponibilidad a futuro (pregunta 20)

¿Les alcanza con ver qué está libre hoy (HU-041) o necesitan el calendario de meses (HU-042)? Si alcanza la vista actual, HU-042 baja a Could. Afecta el [recorrido de UX](../ux/recorrido-disponibilidad-y-reservas.md), que hoy usa el calendario como punto de consulta.

### D-14 Cambio de pagador de una marca (preguntas 14 y 15)

¿Una marca cambia de agencia? ¿La misma marca se compra a veces por dos clientes distintos? Si ambas respuestas son "nunca", se descarta HU-027.

### D-15 Intermediario formal y sus contactos

¿Qué distingue a un intermediario formal de uno común? ¿Qué datos llevan sus contactos? Afecta HU-016 y HU-068.

### D-16 Otras preguntas menores

- **Grupo económico (pregunta 16):** ¿quieren agrupar marcas de un mismo grupo? Afecta HU-017, HU-022 y HU-050.
- **Cambio de razón social de un cliente directo (pregunta 19):** ¿la marca homónima debe actualizarse sola? Afecta HU-018.
- **Interacciones antes de la campaña (pregunta 12):** ¿registran llamadas con una marca antes de que exista una campaña? Afecta HU-020.
- **Dimensiones estándar por formato:** ¿cada formato tiene un tamaño fijo? Afecta HU-009.
- **Formatos sin relevamiento:** ¿cuándo habrá datos de Banderolas, Mediano Formato, Monocolumnas y Carteleras? Afecta HU-015.
- **Usuarios:** ¿quién más, además de Seba y Ale, va a usar el sistema? Afecta HU-004 y HU-005.

---

## Para Administración (no son de esta reunión)

Estas preguntas las responden Seba y Administración. Se listan para no perderlas.

| Tema | Historias | Default |
| --- | --- | --- |
| ¿Administración usa el sistema o solo recibe la planilla? ¿Quién pasa un ítem a Facturado? | HU-065, HU-066, HU-067 | Recibe planilla y avisos por correo; Seba carga el número de factura |
| Alícuotas de IVA y valores de Gob/Priv y F/V | HU-060, HU-061 | 21% por defecto, editable; listas administrables |
| Columnas exactas de la planilla actual | HU-066 | Se reproducen tal cual; las nuevas van al final |
| ¿Se envían los ítems completos aunque haya incompletos en el mes? | HU-066 | Sí; los incompletos se listan con lo que les falta |
| ¿Qué pasa si hay que corregir un ítem ya Facturado? | HU-067 | Sin definir |

## Cómo registrar una respuesta

1. Completar los campos **Respuesta**, **Fecha** y **Quién respondió** de la decisión.
2. Si la respuesta cambia una historia, anotar qué historia y qué cambia, y actualizar `docs/requisitos/historias-de-usuario.md` en un cambio aparte.
3. Si la respuesta es un parámetro configurable (D-01, D-02), anotar también el valor inicial para producción.
4. No cerrar en código una regla afectada mientras su decisión siga pendiente (regla del README).
