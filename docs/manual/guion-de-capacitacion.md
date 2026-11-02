# Guion de capacitación

Guion de la sesión con Seba y Ale (HU-054, criterio 2). La sesión es presencial o por
videollamada, y se graba para poder volver a verla. Dura alrededor de una hora y media: una hora de
recorrido y media hora de preguntas abiertas frente a la pantalla.

## Antes de la sesión

- [ ] Usar **staging**, nunca producción: los ejercicios crean, confirman y cancelan reservas.
- [ ] Staging tiene cargados los datos de ejemplo de `cargar_datos_ejemplo` (se cargan solos al
      arrancar). **Son todos inventados** (regla 6 de [`CLAUDE.md`](../../CLAUDE.md)): ningún
      cliente, marca ni cartel real.
- [ ] Usuarios para practicar: `demo-operativo` (rol Operativo) y `demo-gerencia` (Operativo con
      Gerencia). La contraseña es la de `DJANGO_DEMO_PASSWORD` y se pasa en persona, no por este
      documento.
- [ ] Cada uno tiene a mano el [manual de uso](manual-de-uso.md): la sesión sigue su orden.
- [ ] La grabación está encendida.

## Datos de ejemplo que se usan

| Para | Dato |
| --- | --- |
| Clientes | **Agencia Norte** (Intermediario), **Comercio Directo** (Directo), **Agencia Cordillera** (Intermediario formal, sin contactos todavía), **Distribuidora Andina**, **Medios del Sol** |
| Marcas | **Bebida Fresca** y **Moda Urbana** (de Agencia Norte), **Panadería del Barrio** (de Comercio Directo), **Yogur Valle** (de Agencia Cordillera) |
| Campaña para armar | **Yogur Valle**: Cotizada, con dos reservas Pendientes |
| Campaña para confirmar | **Gaseosa Ola primavera**: Cotizada, de Medios del Sol |
| Carteles LED (varios lugares) | **Av. San Martín 1000** (6 lugares), **Ruta 60 km 5** (4), **Acceso Este km 3** (4) |
| Cartel fijo (un lugar) para el conflicto | Cualquiera que **Disponibilidad › Hoy** muestre **Ocupado** con "1 de 1", por ejemplo **Acceso Este 2500** |

Las fechas de las reservas de ejemplo se calculan desde el día en que se cargaron, así que antes de
la sesión conviene mirar en **Disponibilidad** qué cartel está ocupado y en qué fechas.

## Recorrido

Cada bloque dice qué se muestra, qué hace cada uno en su pantalla y qué tiene que quedar claro.

### 1. Ingreso y menú (5 minutos)

- Ingresar con `demo-operativo`. Mostrar el menú y qué hay en cada grupo.
- Mostrar el **Panel**: ocupación de hoy, campañas activas y por vencer.
- Queda claro: nada se borra; se inactiva, se cancela o se anula.

### 2. Clientes y marcas (10 minutos)

- Crear un cliente nuevo inventado, sin CUIT, para mostrar que nada es obligatorio.
- Crear una marca con un nombre parecido a **Bebida Fresca** (por ejemplo "Bebida fresca") y ver
  el aviso de posible duplicado.
- Abrir **Agencia Cordillera** (Intermediario formal) y cargarle un contacto inventado.
- Queda claro: cliente es a quien se factura; marca es lo que se anuncia.

### 3. Armar una campaña (15 minutos)

- Abrir **Yogur Valle**. Mostrar sus dos reservas Pendientes.
- En **Posiciones por formato**, agregar una línea **LED** con cantidad 3.
- **Agregar carteles**: filtrar, mostrar "ya en la campaña" y "tentativas", elegir dos carteles y
  **Crear reservas**. Ver "LED 3 de 3" y el mensaje "Se crearon 2 reservas Pendientes."
- Cambiar las fechas de la campaña y mostrar la pregunta de mover las Pendientes.
- Queda claro: una Pendiente no le quita el lugar a nadie.

### 4. Confirmar y el conflicto (15 minutos)

- Intentar **Confirmar reservas** con la campaña Cotizada y leer "Primero confirmá la campaña."
- Confirmar **Gaseosa Ola primavera**. Si falta algo, leer el mensaje "Para confirmar falta
  cargar…".
- Agregarle una reserva Pendiente en el cartel fijo ocupado, en fechas que se pisen con la reserva
  que ya tiene.
- **Confirmar reservas**: se confirman las que entran y queda la del conflicto, con quién ocupa el
  cartel.
- Probar la misma reserva como **Nueva reserva** en estado Confirmada y leer el mensaje "sin cupo
  libre (1 de 1)… En conflicto: …".
- Recorrer juntos la tabla de mensajes del [manual](manual-de-uso.md#7-entender-un-mensaje-de-conflicto).
- Queda claro: el lugar es de quien confirma primero, y el mensaje dice con quién se choca.

### 5. Disponibilidad (5 minutos)

- **Hoy**: filtrar por departamento y formato; encontrar un cartel "2 de 1" o una Pendiente que se
  ve pero no bloquea.
- **Calendario**: buscar lugar libre para el mes que viene.

### 6. Ítems a facturar (10 minutos)

- Ingresar con `demo-gerencia`.
- Crear dos ítems del mes: uno completo (cliente y neto) y uno sin cliente.
- Ver el IVA y el total calculados solos.
- **Enviar a facturar**: se envía uno, el otro queda en Borrador con lo que le falta.
- **Descargar planilla** y abrirla juntos: ¿están las columnas que usa Administración?
- **Marcar facturado** con un número de factura inventado, y **Anular** el otro.

## Preguntas abiertas para hacer frente a la pantalla

Son reglas que todavía no están confirmadas. Anotar cada respuesta con fecha y quién la dio; después
el equipo la carga en un PR de historias, con su entrada en el
[registro de cambios](../aidlc/inputs/registro-de-cambios.md).

| Regla | Pregunta | Qué hace hoy el sistema |
| --- | --- | --- |
| RN-001 | Si una reserva termina el 10 y otra empieza el 10 en el mismo cartel, ¿chocan? | Sí, chocan (día compartido pisado) |
| RN-002 | Una reserva Pendiente, ¿debería bloquear el lugar? | No: se ve, pero bloquea recién al confirmar |
| RN-003 | En un LED, ¿el lugar se cuenta por el día más ocupado del período? | Sí, el pico diario |
| RN-006 | ¿Se puede cancelar una reserva confirmada siempre? ¿Con algún aviso o costo? | Siempre se permite y libera el lugar |
| RN-011 | ¿Se puede confirmar una campaña a la que le falta algún dato? | No: exige marca, cliente que factura y fechas |
| RN-015 | ¿Qué clientes tienen varios contactos? | Solo los Intermediario formal |
| RN-018 | ¿Se registran reuniones y llamadas antes de que exista la campaña? | Pendiente de definir |
| RN-021 | ¿Qué usuarios va a haber y con qué rol cada uno? | Pendiente de definir |
| RN-022 | ¿Administración usa el sistema o recibe la planilla? | Recibe la planilla; Seba carga el número de factura |
| RN-023 | ¿Qué alícuotas de IVA se usan además del 21 %? ¿Las listas Gob/Priv y F/V están completas? | 21 % por defecto, editable; listas administrables |
| RN-024 | ¿Las columnas de la planilla son las que usa Administración? **Pedir la planilla real.** | Columnas propuestas por el equipo |
| RN-025 | ¿Se envían los ítems completos aunque haya incompletos en el mes? | Sí; los incompletos se listan con lo que les falta |
| RN-026 | ¿Cómo se corrige un ítem ya facturado? | Pendiente de definir |

## Después de la sesión

- [ ] Subir la grabación a la carpeta compartida de Big Media (no al repositorio) y pegar el enlace
      abajo.
- [ ] Pasar las respuestas de las preguntas abiertas al equipo para el PR de historias.
- [ ] Anotar lo que costó entender, para mejorar este manual.

| Fecha | Participantes | Enlace a la grabación |
| --- | --- | --- |
| | | |
