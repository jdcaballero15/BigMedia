# Manual de uso

Para quienes usan el sistema todos los días. Está organizado por tareas: buscá lo que querés hacer
y seguí los pasos. Los ejemplos usan los datos inventados de prueba, nunca datos reales.

## Cómo está organizada la pantalla

A la izquierda está el menú, con un icono por pantalla. Pasá el mouse por un icono para ver su
nombre; una línea separa cada grupo. Abajo están tu usuario (la inicial) y **Salir**. En el celular,
el botón de arriba a la izquierda abre el menú con los nombres a la vista.

Los grupos son estos:

| Grupo | Pantallas |
| --- | --- |
| Inicio | **Panel**: ocupación de hoy, campañas activas y por vencer |
| Reportes | **Ingresos**, **Por rubro o grupo**, **Ocupación** |
| Comercial | **Clientes**, **Marcas**, **Campañas**, **Interacciones**, **Ítems a facturar** |
| Inventario | **Carteles**, **Disponibilidad** |
| Operación | **Proveedores**, **Costos**, **Formatos** |
| Configuración | **Catálogos**, **Parámetros** |
| Administración | **Auditoría**, **Usuarios** |

Arriba, la barra muestra dónde estás (por ejemplo, «Big Media / Comercial / Clientes») y la
fecha de hoy.

En las tablas, la primera columna (en celeste) es lo que la pantalla lista: el cliente, el cartel,
la campaña. Al final de cada fila queda a la vista la acción principal (**Ver ficha**, **Ver** o
**Editar**, según la pantalla) y el botón de tres puntos (**⋯**) abre el resto: **Inactivar**,
**Dar de baja** y similares. Si el manual nombra una acción que no ves en la fila, está en los tres
puntos. El menú se cierra con Escape o tocando afuera.

Arriba de cada reporte y de Ítems a facturar hay cifras con lo más importante del período; la que
está en azul es la principal. En los reportes, el período se elige con **mes** y **año** de
**Desde** y de **Hasta**; el fin nunca queda antes del inicio.

Lo que podés hacer depende de tu rol: **Operativo** carga y edita; **Lectura** solo consulta;
**Ingresos** y **Auditoría** necesitan además el permiso de Gerencia; **Usuarios** y
**Parámetros** son del administrador.

En el sistema **nada se borra**: los clientes, marcas y carteles se **inactivan** o se dan de baja,
las reservas se **cancelan** y los ítems a facturar se **anulan**. Así queda la historia completa.

## 1. Ingresar

1. Abrí la dirección del sistema que te pasaron.
2. Escribí tu **Usuario** y tu **Contraseña** y tocá **Ingresar**.

- **Primera vez:** el administrador te pasa un link para definir tu contraseña. El link sirve una
  sola vez y vence; si dice "El link no es válido o ya venció", pedile uno nuevo.
- **Si te equivocás varias veces seguidas** (5, salvo que se cambie), el ingreso se bloquea unos
  minutos (15). Esperá y probá de nuevo.
- **Si no usás el sistema un rato**, la sesión se cierra sola y te vuelve a pedir la contraseña.
- Para salir, tocá **Salir** abajo a la izquierda.

## 2. Cargar clientes y marcas

**Cliente** es a quien se le factura. **Marca** es lo que se anuncia; cada marca es de un cliente.

### Cliente nuevo

1. **Comercial › Clientes › Nuevo cliente**.
2. Completá lo que tengas: nombre, razón social, CUIT, tipo (Directo, Intermediario o
   Intermediario formal), teléfono y correo. **Nada es obligatorio**: podés completarlo después.
3. **Guardar cliente**.

- El sistema revisa que el CUIT sea válido y que no esté cargado en otro cliente.
- Un cliente sin nombre aparece como "Cliente sin nombre #12" hasta que se lo pongas.
- Los clientes **Intermediario formal** (agencias grandes) pueden tener varios **contactos**: las
  personas con las que hablás. Uno puede ser el principal.

### Marca nueva

1. **Comercial › Marcas** y creá la marca, eligiendo su cliente y, si querés, su rubro y su grupo
   económico.
2. Si ya existe una marca con un nombre igual o muy parecido, el sistema te avisa ("Ya hay una
   marca con un nombre igual o muy parecido") para que no la cargues dos veces. Revisá la lista y
   decidí.

### Grupos económicos

Un **grupo económico** junta las marcas de un mismo dueño, aunque las facturen clientes distintos
(por ejemplo, dos marcas de la misma empresa que entran por agencias diferentes). Es opcional y cada
marca puede estar en un solo grupo.

- Los grupos se cargan en **Comercial › Marcas**, en la sección **Grupos económicos**, debajo de los
  rubros: **Nuevo grupo económico**, **Renombrar** e **Inactivar**.
- Para asignar una marca a un grupo, editala y elegí el **Grupo económico**.
- En **Reportes › Por rubro o grupo**, **Cortar por: Grupo económico** suma los ingresos y la
  ocupación de todas las marcas de cada grupo.

### Ver la ficha de un cliente o de una marca

- En **Comercial › Clientes**, **Ver ficha** abre la ficha en lugar de la lista. Arriba, en azul,
  están sus datos y cuántas marcas, campañas e interacciones tiene (y contactos, si es
  Intermediario formal). A la izquierda elegís qué ver: **Campañas** (como tarjetas, con filtro por
  estado), **Marcas** o **Interacciones**; debajo, los contactos del Intermediario formal. Sirve
  para tener el contexto antes de llamarlo.
- En **Comercial › Marcas**, **Ver ficha** abre la ficha de la marca: todas sus campañas con su
  estado, aunque las haya pagado otro cliente; sus interacciones (las que tienen la marca cargada y
  las de sus campañas), y, si la marca tiene grupo económico, las otras marcas del grupo.
- Al registrar una interacción en **Comercial › Interacciones** podés elegir una **Marca** del
  cliente aunque todavía no haya campaña, por ejemplo para una primera llamada sobre una marca
  nueva. Si elegís marca, la lista de campañas muestra solo las de esa marca.
- Para volver a la lista, tocá **← Volver** o el nombre de la pantalla en la ruta de arriba (por
  ejemplo, «Clientes» en «Big Media / Comercial / Clientes / Agencia Cordillera»).

## 3. Crear una campaña

Una **campaña** agrupa lo que se le vende a un cliente para una marca: sus reservas, sus costos y lo
que se factura.

1. **Comercial › Campañas › Nueva campaña**.
2. Completá nombre, marca, fechas de inicio y fin y, si hace falta, **Cliente que factura**. Si lo
   dejás en **Según la marca**, factura el cliente dueño de la marca.
3. **Guardar campaña**. Nace en estado **Cotizada**, y mientras está así nada es obligatorio.

Estados de una campaña: **Cotizada** (se está armando), **Confirmada** (el cliente dijo que sí),
**Cancelada** y **Perdida**.

### Confirmar la campaña

1. En la campaña, **Editar**, cambiá el estado a **Confirmada** y guardá.
2. Para confirmar se necesitan **marca, cliente que factura y las dos fechas**. Si falta algo, el
   sistema lo dice; por ejemplo: "Para confirmar falta cargar las fechas."

### Cambiar las fechas de una campaña

Si la campaña tiene reservas Pendientes y le cambiás las fechas, el sistema pregunta:

> La campaña cambió de fechas. ¿Actualizar las 3 reservas Pendientes del 01/12/2026 → 31/12/2026
> a 15/12/2026 → 15/01/2027? Las Confirmadas no se tocan.

- **Actualizar Pendientes** mueve las Pendientes a las fechas nuevas.
- **No, dejarlas** las deja como estaban.

Las reservas Confirmadas nunca se mueven solas: si hay que cambiarlas, se editan una por una.

## 4. Pedir posiciones por formato

En la campaña, la sección **Posiciones por formato** anota cuántos carteles de cada formato pidió
el cliente (por ejemplo, 3 LED y 2 Séxtuples) y cuántos llevás reservados.

1. Elegí el **Formato**, escribí la **Cantidad** (podés dejarla vacía) y tocá **Agregar línea**.
2. La tabla muestra, por formato, **Solicitadas**, **Reservadas** y **Faltantes**. Un formato que
   tiene reservas pero no tiene línea aparece como "(sin línea)".
3. **Editar** cambia la cantidad; **Quitar** saca la línea. Ninguna de las dos toca las reservas
   ya hechas.

## 5. Agregar carteles en tanda

Es la forma rápida de reservar varios carteles del mismo formato para una campaña.

1. En **Posiciones por formato**, tocá **Agregar carteles** en la línea del formato.
2. Revisá **Desde** y **Hasta** (vienen con las fechas de la campaña). Si querés, filtrá por
   **Zona**, **Proveedor** o **Dirección**.
3. La lista muestra **solo los carteles con lugar libre** en esas fechas (los que están fuera de
   servicio no aparecen), con su **Cupo** (cuántos
   lugares ocupados sobre el total) y su **Tarifa de lista**. Al lado del cartel puede decir:
   - "· ya en la campaña": esa campaña ya lo tiene en esas fechas.
   - "· 1 tentativas": hay otra reserva Pendiente en ese cartel; todavía no bloquea, pero puede
     ganarte el lugar si la confirman antes.
4. Tildá los carteles (o **Seleccionar todos los filtrados**). Arriba ves el contador, por ejemplo
   "LED 3 de 3", y el monto estimado.
5. Tocá **Crear reservas**. El sistema avisa cuántas creó, por ejemplo: "Se crearon 2 reservas
   Pendientes."

Las reservas nacen **Pendientes**, con la tarifa de lista del cartel como precio de alquiler. Si un
cartel ya estaba en la campaña con las mismas fechas, no se duplica.

### Una reserva suelta

Para un solo cartel, o para cargar precios de impresión y fijación: sección **Reservas › Nueva
reserva**. Elegí cartel, fechas, estado (Pendiente o Confirmada) y precios, y **Guardar reserva**.
El nombre de la reserva se arma solo: "Marca - Cartel - Mes Año".

## 6. Confirmar las reservas

Una reserva **Pendiente** es una intención: se ve en la disponibilidad, pero no le quita el lugar a
nadie. Una reserva **Confirmada** sí ocupa el lugar, y el sistema no deja confirmar más reservas de
las que entran en el cartel.

### Todas las de la campaña de una vez

1. Confirmá la campaña (ver el punto 3).
2. En **Reservas**, tocá **Confirmar reservas**. Solo aparece con la campaña Confirmada.
3. El sistema confirma las que entran y te lista las que no. Por ejemplo:

   > Se confirmaron 3 reservas.
   > 1 quedó Pendiente por falta de cupo:
   > - Acceso Este 2500, 25/10/2026 → 10/11/2026: ocupado por Campaña #2

Las que quedaron Pendientes no se pierden. Podés cambiarles las fechas, elegir otro cartel o hablar
con quien tiene la otra campaña, y volver a tocar **Confirmar reservas**: solo procesa lo que siga
Pendiente.

### Una por una

En la reserva, **Editar**, cambiá el estado a **Confirmada** y guardá.

### Cancelar o terminar una reserva

En la reserva, **Editar** y cambiá el estado:

- **Cancelada** libera el lugar. Una cancelada se puede volver a confirmar si todavía hay lugar.
- **Finalizada** es una reserva que ya se cumplió.

## 7. Entender un mensaje de conflicto

Cuando algo no se puede hacer, el sistema lo dice en rojo, junto al campo o arriba del formulario.
Los más comunes:

| Mensaje | Qué pasó | Qué hacer |
| --- | --- | --- |
| "Acceso Este 2500: sin cupo libre (1 de 1) entre 2026-10-20 y 2026-11-10. En conflicto: Moda Urbana - Acceso Este 2500 - Oct 2026." | El cartel tiene 1 lugar y ya lo ocupa la reserva "Moda Urbana - Acceso Este 2500 - Oct 2026" en parte de esas fechas | Cambiá las fechas para que no se pisen, elegí otro cartel o, si la otra reserva ya no va, cancelala primero |
| "1 quedó Pendiente por falta de cupo: Acceso Este 2500, 25/10/2026 → 10/11/2026: ocupado por Campaña #2" | Al confirmar la campaña, esa reserva no entró porque otra campaña ocupa el cartel | Lo mismo que el anterior; las demás reservas sí se confirmaron |
| "Primero confirmá la campaña." | Tocaste **Confirmar reservas** con la campaña Cotizada | Confirmá la campaña y volvé a intentar |
| "Para confirmar falta cargar las fechas." | La campaña no tiene todo lo necesario para confirmarse | Cargá lo que dice (marca, cliente que factura o fechas) |
| "El cartel está de baja: no se puede reservar." | El cartel se dio de baja | Elegí otro cartel |
| "El cartel está fuera de servicio (Apagado): no se puede reservar hasta que vuelva a un estado operativo." | El cartel está roto, apagado o en mantenimiento | Elegí otro cartel, o esperá a que vuelva a **Activo** |
| "La fecha de fin no puede ser anterior a la de inicio." | Las fechas están al revés | Corregilas |
| "No se puede pasar de finalizada a confirmada." | Ese cambio de estado no está permitido | Una Finalizada no cambia; para otra venta, creá una reserva nueva |

**Cómo se cuentan los lugares.** Cada cartel tiene una capacidad: 1 en la mayoría de los fijos y
varios en los LED y los séxtuples (por ejemplo, "0 de 6" son 6 lugares libres). Para ver si una
reserva entra, el sistema mira el día más ocupado del período. El día en que una reserva termina y
otra empieza **cuenta como pisado**: si una termina el 10 y la otra empieza el 10, chocan. Estas
reglas todavía pueden cambiar (RN-001 a RN-003); si cambian, el manual se actualiza.

## 8. Ver la disponibilidad

**Inventario › Disponibilidad** tiene dos vistas:

- **Hoy**: qué carteles están **Libres** u **Ocupados** en este momento, con su ocupación (por
  ejemplo "1 de 6"). Se filtra por departamento, formato y modalidad.
- **Calendario**: los carteles mes por mes, para ver qué queda libre a futuro. Cada celda es una
  barra que se llena según lo ocupado ("1/6"), y queda en ámbar cuando el cartel está lleno.
  Tocá una celda ocupada para ver la campaña.

Las dos vistas se eligen arriba a la derecha.

La ocupación cuenta también las reservas Pendientes, para que se vean. Por eso un cartel puede
mostrar "2 de 1" si tiene una Confirmada y una Pendiente que se pisan: la Pendiente no va a poder
confirmarse hasta que se libere el lugar.

### Un cartel que se rompe o se apaga

En **Inventario › Carteles**, tocá **Editar** en el cartel y cambiá su **Estado** (por ejemplo a
**Apagado**, **En mantenimiento** o **Vidrio destruido**). Al guardar:

- Si el cartel tiene reservas activas (Pendientes o Confirmadas que todavía no terminaron), aparece
  un aviso con la lista: reserva, campaña, fechas y estado. Esas reservas **no se tocan**: decidí
  si las pasás a otro cartel o si avisás al cliente. Si no tiene ninguna, el aviso lo dice.
- El aviso sale solo cuando cambia el estado: si editás otro dato de un cartel que ya estaba
  apagado, no vuelve a aparecer.
- Mientras el cartel no vuelva a **Activo**, no se le pueden cargar reservas nuevas: no aparece al
  elegir cartel ni en **Agregar carteles**.
- Las reservas que ya tenía se pueden seguir editando y confirmando.

## 9. Cargar los ítems a facturar y enviar el mes

Cada vez que llega una orden de compra, cargás lo que hay que facturar. A fin de mes, lo enviás a
Administración.

### Cargar un ítem

1. **Comercial › Ítems a facturar › Nuevo ítem**.
2. Completá mes de facturación, cliente, marca, campaña, descripción del servicio, período, cantidad
   y precio unitario, tipo de servicio y de soporte, sector (Gob/Priv) y tipo de venta (F/V).
   **Nada es obligatorio mientras está en Borrador.**
3. **Importe neto:** si lo dejás vacío, se calcula como cantidad × precio unitario.
4. **IVA y total** se calculan solos con la alícuota (21 % si no la cambiás).
5. **Guardar ítem**. Nace en **Borrador**.

Arriba de la lista ves los totales del mes (neto, IVA, total, costos y neto final), sin contar los
anulados.

### Costos del ítem

Guardá el ítem y volvé a **Editar**: abajo está **Costos del ítem**.

1. Elegí el **Tipo de costo** (por ejemplo, Comisión o Impresión) y **Cómo se calcula**: **Monto
   fijo** o **Porcentaje del neto**. Con un 15 % sobre un neto de $10.000, el costo es $1.500.
2. Indicá a quién se le paga: un **Proveedor** o, si no lo es, escribilo en **A quién se le paga**.
3. Tocá **Agregar costo**.

- Si cambiás el importe neto, los costos en porcentaje se recalculan solos.
- Si el ítem tiene campaña, podés **Vincular** un costo ya cargado en una de sus reservas. No se
  copia: es el mismo costo, así la rentabilidad de la campaña lo cuenta una sola vez.
- **Anular** un costo pide un motivo; deja de sumar pero queda a la vista. Un costo de reserva
  vinculado se anula desde **Costos**.

La lista muestra el **costo total** y el **neto final** (neto menos costos) de cada ítem, y la
planilla los suma al final.

### Orden de compra

- En el ítem cargá el **Número de orden de compra** y su **Fecha de aprobación**.
- Para adjuntar el **PDF de la orden de compra**, guardá el ítem primero y volvé a **Editar**. Solo
  se aceptan PDF de hasta 5 MB. Desde el formulario podés abrirlo o quitarlo, y en la lista aparece
  el enlace **PDF**.
- Si el número de OC ya está cargado en otro ítem, el sistema lo guarda igual y te avisa en cuál
  está, por si es un duplicado.

### Varios ítems en una misma factura

1. Marcá los ítems en Borrador del mismo mes que van juntos.
2. Tocá **Agrupar en una factura**. Comparten un grupo (por ejemplo, G-12), que se ve en la columna
   **Grupo** y en la planilla, donde salen juntos.
3. **Quitar del grupo** deja un ítem independiente.

El CUIT de facturación del ítem puede ser distinto del CUIT del cliente: la planilla muestra el del
ítem.

### Enviar el mes a facturar

1. Elegí el **Mes** y tocá **Enviar a facturar**.
2. Se envían los Borradores **completos**: los que tienen cliente, importe neto y mes. Los demás
   quedan en Borrador y el sistema te dice qué les falta. Por ejemplo:

   > Se enviaron 5 ítems a facturar. Descargar planilla
   > 1 quedó en Borrador porque le falta: Impresión lona Vendimia: cliente, importe neto

3. **Descargar planilla** baja el .xlsx de ese envío para Administración. Cada envío queda
   registrado en **Envíos a facturar**, con quién lo mandó y cuándo, y su planilla se puede volver
   a bajar.

Si no hay ningún ítem completo, dice "No hay ítems completos para enviar." y no se envía nada.

### Después del envío

- Cuando Administración factura, tocá **Marcar facturado** en el ítem, escribí el **Número de
  factura** y confirmá (sin número no se puede marcar).
- **Anular** saca un ítem que no va. Se puede anular en Borrador o en Enviado.
- Un ítem enviado ya no se edita. Para corregirlo, tocá **Reabrir**, escribí el **Motivo de la
  reapertura** y tocá **Confirmar reapertura**. Vuelve a Borrador, queda registrado quién, cuándo y
  por qué, y Administración recibe un correo para que no lo facture todavía.
- Corregí el ítem y volvé a tocar **Enviar a facturar** del mes. Sale de nuevo como Enviado, con la
  marca **Reenviado** en la lista y en la planilla, y Administración recibe otro correo con los
  valores anteriores y nuevos de lo que cambió.
- Un ítem ya facturado no se reabre. Si hay que corregirlo (por ejemplo, porque Administración
  emitió la nota de crédito), tocá **Anular**, escribí el **Motivo de la anulación** y tocá
  **Confirmar anulación**. Pasa a Anulado conservando su número de factura, sale del resumen del
  mes, queda registrado quién, cuándo y por qué, y Administración recibe un correo. Después cargá
  la corrección como un ítem nuevo.

## Preguntas frecuentes

**¿Puedo borrar algo que cargué mal?**
No desde la aplicación. Inactivá el cliente o la marca, cancelá la reserva o anulá el ítem. Si
realmente hay que borrar un error de carga, lo hace el administrador desde el panel de
administración, y queda registrado en la auditoría.

**Creé reservas en tanda y no las veo en la disponibilidad como ocupadas.**
Sí se ven, pero como Pendientes. Recién ocupan el lugar de verdad al confirmarlas.

**Confirmé la campaña, ¿se confirmaron las reservas?**
No. Confirmar la campaña habilita el botón **Confirmar reservas**; las reservas se confirman al
tocarlo.

**Otra persona me ganó el lugar mientras yo armaba la campaña.**
Puede pasar: el lugar es de la reserva que se confirma primero. El mensaje te dice qué reserva lo
ocupa, para que puedan hablarlo.

**¿Quién cambió este dato?**
**Administración › Auditoría** (con permiso de Gerencia) muestra cada cambio, con quién lo hizo y
cuándo.

**El sistema me volvió a pedir la contraseña.**
La sesión se cierra sola después de un rato sin uso (30 minutos, salvo que se cambie). Volvé a
ingresar; lo que ya estaba guardado no se pierde.

**Encontré algo que no anda o necesito algo nuevo.**
Contáselo al equipo con fecha, en qué pantalla estabas y qué esperabas que pasara. Si podés, sumá
una captura.
