# Reglas de negocio

Catálogo vivo de las reglas que el sistema aplica, con su estado. Cuando una regla cambia, se
actualiza acá, en la historia afectada y en el registro de cambios
([`inputs/registro-de-cambios.md`](inputs/registro-de-cambios.md)), en el mismo PR.

- **Estados:** `pendiente` (sin respuesta ni valor usable) · `provisoria` (se usa un valor razonable
  hasta que Big Media confirme) · `confirmada` · `reemplazada por RN-xxx`.
- **IDs:** nunca se reutilizan. Las reglas que vienen de las decisiones del 15/10 conservan su
  número viejo entre paréntesis (D-xx).
- **Tests:** los que verifican una regla llevan `@pytest.mark.regla("RN-xxx")`.
  `pytest -m regla` los lista todos.
- Lo que está en `provisoria` se implementa, en lo posible, como parámetro configurable (HU-001).

15 de octubre de 2026 · Fuente: [historias de usuario](inputs/historias-de-usuario.md)

Este catálogo ordena por prioridad las reglas de negocio que nacieron como decisiones pendientes en las historias de usuario. Para cada una indica qué parte del sistema queda bloqueada, qué default se usa mientras tanto y dónde anotar la respuesta.

Las historias citan "preguntas" numeradas (por ejemplo, "pregunta 10"). Esa lista numerada no está en el repositorio; acá se las nombra por tema y se conserva el número entre paréntesis cuando la historia lo menciona.

## Cómo se priorizó

- **P1 — Bloquea el núcleo.** Sin la respuesta no se puede cerrar el motor de disponibilidad (épica E5), el modelo de datos del cartel o la reserva, ni sus pruebas automáticas. Un cambio posterior obliga a migrar datos o reescribir la validación.
- **P2 — Bloquea una historia Must o la carga inicial.** Hay un default razonable, pero condiciona la importación del inventario o un flujo central de campañas.
- **P3 — Ajusta detalles.** Afecta historias Should o Could, o se puede cambiar después por configuración sin costo alto.

## Resumen

| ID | Regla | Estado | Valor actual | Origen | HUs | Dónde vive |
| --- | --- | --- | --- | --- | --- | --- |
| RN-001 | Día límite entre reservas | `provisoria` | Inclusivo: el día compartido se pisa | Documento de historias (decisión D-01 del 15/10/2026) | HU-001, HU-031, HU-033, HU-040, HU-042, HU-051 | Servicio `apps/reservas/services.py` (fin efectivo), modelo `ParametrosDisponibilidad.borde_inclusivo` (pantalla Parámetros), `backend/tests/test_disponibilidad.py`, `backend/tests/test_parametros.py`; lista de "Agregar carteles" `apps/reservas/services.py::carteles_para_tanda`, `backend/tests/test_carteles_para_tanda.py` |
| RN-002 | ¿Una reserva Pendiente bloquea a otras? | `provisoria` | Ocupa cupo solo visualmente; bloqueo duro al confirmar | Documento de historias (decisión D-02 del 15/10/2026) | HU-001, HU-031, HU-033, HU-041, HU-042, HU-056, HU-059 | Servicio `apps/reservas/services.py` (estados que bloquean), modelo `ParametrosDisponibilidad.tentativa_bloquea` (pantalla Parámetros), `backend/tests/test_disponibilidad.py`, `backend/tests/test_parametros.py`; lista de "Agregar carteles" `carteles_para_tanda` y creación en bloque `crear_reservas_en_bloque` (no valida cupo al crear Pendientes), `backend/tests/test_carteles_para_tanda.py`, `backend/tests/test_reservas_en_bloque.py` |
| RN-003 | Cómo se cuentan los cupos dentro de un rango | `provisoria` | Pico diario: ocupación máxima por tramo del rango | Juan Diego (2026-10-19), sobre la decisión D-03 del 15/10/2026 | HU-031, HU-032, HU-034, HU-040, HU-042, HU-056 | Servicio `apps/reservas/services.py::validar_disponibilidad` (pico diario), `backend/tests/test_disponibilidad.py`; lista de "Agregar carteles" `carteles_para_tanda` (reusa `_pico_en_rango`), `backend/tests/test_carteles_para_tanda.py` |
| RN-004 | Cupos de los LED | `provisoria` | Capacidad editable por cartel; una reserva = un cupo | Documento de historias (decisión D-04 del 15/10/2026) | HU-011, HU-028, HU-031, HU-034, HU-040, HU-048, HU-057 | `Formato.capacidad_predeterminada`, `Cartel.capacidad`, `backend/tests/test_carteles.py` |
| RN-005 | Slots de los séxtuples | `provisoria` | Capacidad = slots relevados; una reserva = un slot genérico | Documento de historias (decisión D-05 del 15/10/2026) | HU-010, HU-011, HU-015, HU-030, HU-031, HU-057 | `Formato.capacidad_predeterminada`, `Cartel.capacidad`, `backend/tests/test_carteles.py` |
| RN-006 | Reglas de cancelación | `provisoria` | Cancelar siempre se permite y libera el cupo | Documento de historias (decisión D-06 del 15/10/2026) | HU-024, HU-035, HU-037, HU-045, HU-051, HU-058, HU-060 | Sin implementar |
| RN-007 | Propiedad de los carteles | `provisoria` | Costos solo de impresión y fijación | Documento de historias (decisión D-07 del 15/10/2026) | HU-010, HU-015, HU-043, HU-044, HU-046 | Modelo `Costo` y margen en `apps/costos/` (default informativo; HU-046 terceros pendiente) |
| RN-008 | Lista de zonas (departamentos) | `confirmada` | Los nueve departamentos (Ciudad, Godoy Cruz, Maipú, Luján de Cuyo, Guaymallén, Las Heras, San Martín, Rivadavia, San Carlos) | Juan Diego, 15/10/2026, diseño de inventario | HU-010, HU-013, HU-014, HU-015, HU-048 | Migración `inventario/0002_catalogos_iniciales`, catálogo editable |
| RN-009 | Contenido real de los relevamientos | `pendiente` | Sin carga hasta tener los archivos | Documento de historias (decisión D-09 del 15/10/2026) | HU-015 | Sin implementar |
| RN-010 | Estados físicos y carteles fuera de servicio | `provisoria` | Alertar y bloquear reservas nuevas | Documento de historias (decisión D-10 del 15/10/2026) | HU-012, HU-039 | Modelo `EstadoCartel`, migración `0002_catalogos_iniciales` (los cinco estados) |
| RN-011 | ¿Se puede confirmar una campaña incompleta? | `provisoria` | Se exigen cliente, marca y fechas | Documento de historias (decisión D-11 del 15/10/2026) | HU-024, HU-030, HU-049, HU-059 | Parcial: `apps/campanias/services.py::validar_confirmacion` y su test `test_confirmar_exige_marca_cliente_y_fechas`; la confirmación en bloque de reservas (HU-059) queda para E5 |
| RN-012 | Reservas con fechas pasadas | `provisoria` | No se permite a mano; histórico solo por importación | Documento de historias (decisión D-12 del 15/10/2026) | HU-038, HU-048, HU-049 | Sin implementar |
| RN-013 | Vista de disponibilidad a futuro | `provisoria` | Se construye como Should | Documento de historias (decisión D-13 del 15/10/2026) | HU-041, HU-042 | Sin implementar |
| RN-014 | Cambio de pagador de una marca | `provisoria` | La campaña puede llevar un cliente que factura propio que reemplaza la deducción desde la marca; HU-027 sigue viva | Seba (2026-10-19), sobre la decisión D-14 del 15/10/2026 | HU-027 | Modelo `Campania.cliente_facturacion` y propiedad `cliente_factura` (unidad campanias) |
| RN-015 | Intermediario formal y sus contactos | `provisoria` | Tipo aparte con contactos múltiples | Documento de historias (decisión D-15 del 15/10/2026) | HU-016, HU-068 | Servicio `apps/clientes/services.py` (`acepta_contactos`, `guardar_contacto`), modelo `Contacto`, `backend/tests/test_contactos.py` |
| RN-016 | Grupo económico | `pendiente` | Sin definir | Documento de historias (decisión D-16 del 15/10/2026) | HU-017, HU-022, HU-050 | Sin implementar |
| RN-017 | Cambio de razón social de un cliente directo | `pendiente` | Sin definir | Documento de historias (decisión D-16 del 15/10/2026) | HU-018 | Sin implementar |
| RN-018 | Interacciones antes de la campaña | `pendiente` | Sin definir | Documento de historias (decisión D-16 del 15/10/2026) | HU-020 | Sin implementar |
| RN-019 | Dimensiones estándar por formato | `pendiente` | Sin definir | Documento de historias (decisión D-16 del 15/10/2026) | HU-009 | Sin implementar |
| RN-020 | Formatos sin relevamiento | `pendiente` | Sin definir | Documento de historias (decisión D-16 del 15/10/2026) | HU-015 | Sin implementar |
| RN-021 | Usuarios | `pendiente` | Sin definir | Documento de historias (decisión D-16 del 15/10/2026) | HU-004, HU-005 | Sin implementar |
| RN-022 | Administración usa el sistema o recibe planilla | `provisoria` | Recibe planilla y avisos por correo; Seba carga el número de factura | Documento de historias (bloque Administración del 15/10/2026) | HU-065, HU-066, HU-067 | El operativo pasa el ítem a Facturado con su número (`apps/facturacion/services.py::validar_cambio_de_item`, `backend/tests/test_estados_facturacion.py`) y envía el mes descargando la planilla (`enviar_a_facturar`, `backend/tests/test_cierre_de_mes.py`); los avisos por correo esperan HU-067 |
| RN-023 | Alícuotas de IVA y listas Gob/Priv y F/V | `provisoria` | 21% por defecto, editable; listas administrables | Documento de historias (bloque Administración del 15/10/2026) | HU-060, HU-061 | `apps/facturacion/models.py` (`alicuota_iva` con 21 % por defecto, `iva_y_total`; catálogos `Sector` y `TipoVenta` administrables en el admin), `backend/tests/test_importes_facturacion.py` |
| RN-024 | Columnas de la planilla de facturación | `provisoria` | Se reproducen tal cual; las nuevas van al final | Documento de historias (bloque Administración del 15/10/2026) | HU-066 | `apps/facturacion/services.py::COLUMNAS_PLANILLA` (columnas propuestas hasta tener la planilla real), `backend/tests/test_planilla_facturacion.py` |
| RN-025 | Envío de ítems completos con incompletos en el mes | `provisoria` | Sí; los incompletos se listan con lo que les falta | Documento de historias (bloque Administración del 15/10/2026) | HU-066 | `apps/facturacion/services.py::enviar_a_facturar` y `faltantes_para_enviar`, `backend/tests/test_cierre_de_mes.py` |
| RN-026 | Corrección de ítems ya facturados | `pendiente` | Sin definir | Documento de historias (bloque Administración del 15/10/2026) | HU-067 | Sin implementar |

Las reglas de Administración (facturación) están al final, en un bloque aparte.

---

## P1 — Bloquean el núcleo

### RN-001 Día límite entre reservas (día de borde) (D-01)

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

### RN-002 ¿Una reserva Pendiente bloquea a otras? (D-02)

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

### RN-003 Cómo se cuentan los cupos dentro de un rango (D-03)

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

**Respuesta:** pico diario (ocupación máxima por tramo): es exacto y no rechaza reservas que en
realidad entran; coincide con el diseño de `units/base-del-repositorio.md`. · **Fecha:** 2026-10-19 ·
**Quién respondió:** Juan Diego

### RN-004 Cupos de los LED (D-04)

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

### RN-005 Slots de los séxtuples (D-05)

**Preguntas.**

1. Cuando una marca compra un séxtuple, ¿compra un slot cualquiera o un slot concreto (por ejemplo, "el de arriba a la izquierda")?
2. ¿Una marca puede ocupar más de un slot del mismo séxtuple a la vez?
3. Si se rompe un slot, ¿baja la capacidad del cartel o se marca el slot como fuera de servicio?
4. Big Media identifica un séxtuple por Dirección + cantidad de slots (HU-010). Si el séxtuple cambia de 6 a 4 slots, ¿es el mismo cartel? ¿Puede haber dos séxtuples en la misma dirección?
5. ¿Hay alguna restricción entre marcas que comparten un séxtuple, por ejemplo competidores directos? (No figura en las historias; preguntarlo solo para descartarlo.)

**Por qué importa.** Si el cliente elige un slot concreto, la reserva necesita guardar qué slot ocupa y la validación pasa de "hay cupo" a "este slot está libre". Además, si la cantidad de slots es parte de la identidad del cartel, cambiarla puede crear un duplicado en la importación.

**Default.** La capacidad es igual a los slots relevados (HU-015) y cada reserva ocupa un slot genérico, sin posición.

**Input de Seba (2026-10-19).** Confirma el default y lo amplía más allá de los séxtuples: en los circuitos grandes (séxtuples, séptuples, PPL, banderolas, carteleras) **no** quiere que el sistema lo obligue a cargar la posición exacta de cada cartel; esa gestión la sigue haciendo aparte. Para esos casos quiere algo simple: **cantidad + tipo de cartel + importes**. Queda por confirmar con Juan Diego si esto cierra RN-005 como `confirmada` para E5 y si "séptuples" es un formato nuevo a sumar al inventario (hoy no está en los siete formatos).

**Bloquea.**

- Clave para detectar duplicados en la importación de los 226 séxtuples (HU-015, ver [importación](inputs/importacion/README.md)).
- Nombre legible del cartel (HU-010) y de la reserva (HU-030).
- Reducción de capacidad con reservas a futuro (HU-011).
- Validación (HU-031) y creación en bloque (HU-057).

**Respuesta:** slot genérico, sin posición exacta, para todos los circuitos grandes (input de Seba; ver arriba). · **Fecha:** 2026-10-19 · **Quién respondió:** Seba (relevado por el equipo)

### RN-006 Reglas de cancelación (D-06)

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

### RN-007 Propiedad de los carteles (D-07)

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

### RN-008 Lista de zonas (departamentos) (D-08)

**Pregunta.** ¿Cuáles son los 9 departamentos de Mendoza en los que hay carteles, escritos exactamente como los usan? ¿Hace falta una zona más fina, como un barrio o un corredor?

**Bloquea.** La zona es obligatoria en el cartel (HU-010), así que sin esta lista no se puede importar ningún cartel (HU-015). También afecta los filtros del inventario y de los reportes (HU-013, HU-014, HU-048).

**Default.** Lista vacía y administrable.

**Respuesta:** Los nueve departamentos: Ciudad, Godoy Cruz, Maipú, Luján de Cuyo, Guaymallén, Las Heras, San Martín, Rivadavia y San Carlos. Se cargan como catálogo editable · **Fecha:** 15/10/2026 · **Quién respondió:** Juan Diego, en el diseño de inventario

### RN-009 Contenido real de los relevamientos (D-09)

**Preguntas.**

1. ¿Pueden compartir las planillas de Gran Formato (66 o más posiciones) y de Séxtuples (226 posiciones) tal como están hoy?
2. En Gran Formato, ¿el tamaño se escribe siempre como ancho × alto en metros (por ejemplo "6x3")?
3. ¿Los colores o celdas combinadas de la planilla significan algo (estado, cliente actual, proveedor)?
4. ¿Las planillas tienen tarifa de lista, proveedor o foto, o eso se completa después?
5. ¿Hay carteles que figuran dos veces a propósito, por ejemplo dos caras en la misma dirección?

**Bloquea.** La transformación a la [plantilla CSV](inputs/importacion/README.md) y las reglas de duplicados (HU-015).

**Default.** No se carga nada hasta tener los archivos. No se inventan datos.

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

### RN-010 Estados físicos y carteles fuera de servicio (preguntas 9 y 18) (D-10)

**Preguntas.**

1. Además de Activo, En mantenimiento, De baja, Apagado y Vidrio destruido, ¿hay otros estados?
2. Si un cartel con reservas confirmadas se rompe, ¿qué hacen hoy? ¿Reubican a la marca en otro cartel, acortan la reserva o la cancelan?
3. ¿Un cartel en mantenimiento puede recibir reservas para fechas futuras, cuando ya esté reparado?

**Default.** Se alerta, se listan las reservas afectadas sin modificarlas y se bloquean las reservas nuevas mientras el cartel no esté operativo.

**Bloquea.** Estados del cartel (HU-012), alertas (HU-039), caso 16 de la matriz de pruebas y la columna `estado` de la importación.

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

### RN-011 ¿Se puede confirmar una campaña incompleta? (D-11)

**Pregunta.** ¿Alguna vez confirman una campaña sin saber todavía la marca o quién factura?

**Default.** Para confirmar se exigen cliente que factura, marca y fechas (HU-059). Si Seba prefiere permitirlo, se quita la exigencia y los reportes muestran un grupo "(vacío)".

**Bloquea.** Confirmación de campaña (HU-024, HU-059), nombre de las reservas "Sin marca" (HU-030) y reportes por cliente y marca (HU-049).

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

### RN-012 Reservas con fechas pasadas (preguntas 8 y 11) (D-12)

**Preguntas.**

1. ¿Existe un histórico de reservas? ¿En qué formato, de cuántos años y con qué calidad?
2. ¿Un operativo necesita cargar a mano una reserva que ya ocurrió, por ejemplo una que se olvidó registrar?

**Default.** Las históricas entran como Finalizadas solo por importación (HU-038). La carga manual con fecha pasada no se permite.

**Bloquea.** Importación histórica (HU-038) y reportes con comparativo interanual (HU-048, HU-049).

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

---

## P3 — Ajustan detalles

### RN-013 Vista de disponibilidad a futuro (pregunta 20) (D-13)

¿Les alcanza con ver qué está libre hoy (HU-041) o necesitan el calendario de meses (HU-042)? Si alcanza la vista actual, HU-042 baja a Could. Afecta el [recorrido de UX](inputs/ux/recorrido-disponibilidad-y-reservas.md), que hoy usa el calendario como punto de consulta.

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**


### RN-014 Cambio de pagador de una marca (preguntas 14 y 15) (D-14)

¿Una marca cambia de agencia? ¿La misma marca se compra a veces por dos clientes distintos? Si ambas respuestas son "nunca", se descarta HU-027.

**Respuesta:** sí puede pasar: una marca cambia de agencia o la compran dos clientes distintos. Por eso la campaña lleva un `cliente_facturacion` propio y opcional que, cuando se carga, reemplaza la deducción desde la marca; vacío, se deduce de la marca. HU-027 sigue viva. · **Fecha:** 2026-10-19 · **Quién respondió:** Seba (relevado por el equipo)


### RN-015 Intermediario formal y sus contactos (D-15)

¿Qué distingue a un intermediario formal de uno común? ¿Qué datos llevan sus contactos? Afecta HU-016 y HU-068.

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

### RN-016 Grupo económico (D-16)

Pregunta menor del bloque «Otras preguntas menores» de D-16.

**Grupo económico (pregunta 16):** ¿quieren agrupar marcas de un mismo grupo? Afecta HU-017, HU-022 y HU-050.

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

### RN-017 Cambio de razón social de un cliente directo (D-16)

Pregunta menor del bloque «Otras preguntas menores» de D-16.

**Cambio de razón social de un cliente directo (pregunta 19):** ¿la marca homónima debe actualizarse sola? Afecta HU-018.

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

### RN-018 Interacciones antes de la campaña (D-16)

Pregunta menor del bloque «Otras preguntas menores» de D-16.

**Interacciones antes de la campaña (pregunta 12):** ¿registran llamadas con una marca antes de que exista una campaña? Afecta HU-020.

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

### RN-019 Dimensiones estándar por formato (D-16)

Pregunta menor del bloque «Otras preguntas menores» de D-16.

**Dimensiones estándar por formato:** ¿cada formato tiene un tamaño fijo? Afecta HU-009.

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

### RN-020 Formatos sin relevamiento (D-16)

Pregunta menor del bloque «Otras preguntas menores» de D-16.

**Formatos sin relevamiento:** ¿cuándo habrá datos de Banderolas, Mediano Formato, Monocolumnas y Carteleras? Afecta HU-015.

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

### RN-021 Usuarios (D-16)

Pregunta menor del bloque «Otras preguntas menores» de D-16.

**Usuarios:** ¿quién más, además de Seba y Ale, va a usar el sistema? Afecta HU-004 y HU-005.

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

---

## Para Administración (no son de esta reunión)

Estas preguntas las responden Seba y Administración. Se listan para no perderlas.

### RN-022 Administración usa el sistema o recibe planilla

**Tema.** ¿Administración usa el sistema o solo recibe la planilla? ¿Quién pasa un ítem a Facturado?

**Historias.** HU-065, HU-066, HU-067.

**Default.** Recibe planilla y avisos por correo; Seba carga el número de factura.

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

### RN-023 Alícuotas de IVA y listas Gob/Priv y F/V

**Tema.** Alícuotas de IVA y valores de Gob/Priv y F/V

**Historias.** HU-060, HU-061.

**Default.** 21% por defecto, editable; listas administrables.

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

### RN-024 Columnas de la planilla de facturación

**Tema.** Columnas exactas de la planilla actual

**Historias.** HU-066.

**Default.** Se reproducen tal cual; las nuevas van al final.

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

### RN-025 Envío de ítems completos con incompletos en el mes

**Tema.** ¿Se envían los ítems completos aunque haya incompletos en el mes?

**Historias.** HU-066.

**Default.** Sí; los incompletos se listan con lo que les falta.

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

### RN-026 Corrección de ítems ya facturados

**Tema.** ¿Qué pasa si hay que corregir un ítem ya Facturado?

**Historias.** HU-067.

**Default.** Sin definir.

**Respuesta:** _pendiente_ · **Fecha:** · **Quién respondió:**

---

## Cómo registrar una respuesta

1. Cargar o actualizar el issue del pedido (plantilla "Pedido de Seba").
2. En un PR `docs/historias-<descripcion>`: cambiar el estado y el valor de la regla, completar
   **Respuesta**, **Fecha** y **Quién respondió**, actualizar las historias afectadas y agregar
   una fila al registro de cambios.
3. Si la regla es un parámetro configurable (RN-001, RN-002), anotar el valor inicial para producción.
4. Si ya hay código que aplica la regla, el cambio de código va en una unidad aparte
   (`ajuste-<tema>`) que cierra el issue.
