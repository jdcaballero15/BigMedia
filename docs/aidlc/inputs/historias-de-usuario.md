# Historias de usuario - Sistema de reservas OOH (desarrollo a medida)

Oct 14, 2026 · @Juan Diego

Este documento define 68 historias de usuario, agrupadas en 12 épicas, que cubren los requisitos vigentes del sistema de reservas de espacios publicitarios de vía pública (OOH) de Big Media Argentina, pensado como una aplicación desarrollada desde cero y sin dependencia de una plataforma de terceros. El objetivo central es **evitar la doble reserva de un cartel en fechas superpuestas** y conservar un historial que permita analizar la rentabilidad por cartel y por cliente.

## Cómo leer las historias

**Actores**

- **Operativo:** Seba y Ale, quienes cargan y consultan el día a día.
- **Administrador:** persona de Big Media con control total del sistema.
- **Gerencia:** Gonzalo y Diego, quienes consultan reportes.
- **Sistema:** procesos automáticos (tareas programadas, validaciones del servidor).
- **Equipo de desarrollo:** quienes construyen y mantienen el sistema. Además, Administración (área de Big Media que factura) recibe la planilla de cierre de mes (HU-066); si necesita usuario propio es una pregunta abierta.

**Prioridad (MoSCoW):** Must = sin esto el sistema no cumple su objetivo; Should = importante pero con alternativa temporal; Could = deseable, depende de una respuesta pendiente del cliente.

**Complejidad (estimación relativa, preliminar):** S = hasta 1 día; M = 2 a 3 días; L = alrededor de 1 semana; XL = más de 1 semana o con riesgo técnico alto.

**Entidades del negocio:** Proveedor, Formato, Cartel, Cliente, Marca, Campaña, Reserva, Ítem de facturación, Costo, Interacción y Usuario. Cada historia respeta la regla transversal de que ningún dato de negocio se borra físicamente: se inactiva o se cancela.

## Mapa de épicas

| Épica | Nombre | Historias |
| --- | --- | --- |
| E0 | Plataforma base | HU-001 a HU-002 |
| E1 | Seguridad y acceso | HU-003 a HU-007 |
| E2 | Inventario de soportes | HU-008 a HU-015 |
| E3 | Clientes, marcas y CRM | HU-016 a HU-022 y HU-068 |
| E4 | Campañas | HU-023 a HU-027 |
| E5 | Reservas y motor de disponibilidad | HU-028 a HU-040 |
| E6 | Vista de disponibilidad | HU-041 a HU-042 |
| E7 | Costos y rentabilidad | HU-043 a HU-046 |
| E8 | Reportes y paneles | HU-047 a HU-052 |
| E9 | Entrega y traspaso | HU-053 a HU-054 |
| E10 | Armado de campañas y reserva masiva | HU-055 a HU-059 |
| E11 | Facturación mensual | HU-060 a HU-067 |

La épica E5 es el núcleo del sistema: si hay que recortar alcance, se recorta alrededor de ella y nunca adentro.

# E0 - Plataforma base

### HU-001 Parámetros de comportamiento configurables

- **Actor:** Administrador
- **Descripción:** Como administrador, quiero configurar desde el sistema si una reserva tentativa ocupa cupo y si el día de borde se pisa, para ajustar las reglas de disponibilidad sin pedir un cambio de código.
- **Prioridad:** Should
- **Complejidad:** S
- **Precondición:** El administrador tiene sesión iniciada con permiso de configuración.
- **Regla de negocio:** Hay dos parámetros: "la tentativa ocupa cupo" (sí o no) y "día de borde inclusivo" (sí o no; con inclusivo, si una reserva termina el 15 y otra empieza el 15, se pisan). Defaults provisorios hasta que Seba responda: la tentativa ocupa cupo visualmente y el borde es inclusivo.
- **Criterios de aceptación:**
  1. Dada la pantalla de configuración, cuando el administrador cambia un parámetro y guarda, entonces la validación de disponibilidad usa el nuevo valor de inmediato, sin reiniciar nada.
  2. Dado un usuario sin rol de administrador, cuando intenta abrir la configuración, entonces no tiene acceso.
  3. Dado un cambio de parámetro, cuando se guarda, entonces queda registrado quién lo cambió y cuándo (ver HU-007).

### HU-002 Entornos, migraciones y respaldo

- **Actor:** Equipo de desarrollo
- **Descripción:** Como equipo de desarrollo, quiero entornos separados (desarrollo, pruebas y producción), cambios de esquema versionados y respaldos automáticos, para publicar sin romper los datos reales y recuperar el sistema ante una falla.
- **Prioridad:** Must
- **Complejidad:** M
- **Precondición:** Repositorio de código y servidor de producción definidos por Big Media.
- **Regla de negocio:** El código y los datos son propiedad de Big Media. Todo cambio en la estructura de datos se aplica mediante migraciones versionadas y reversibles; nunca a mano en producción.
- **Criterios de aceptación:**
  1. Dado un cambio aprobado, cuando se publica, entonces el despliegue corre de forma automatizada en pruebas antes de pasar a producción.
  2. Dada una migración de esquema, cuando se aplica en un entorno limpio, entonces reconstruye la estructura completa sin pasos manuales.
  3. Dado producción, cuando pasa un día, entonces existe un respaldo automático verificable y se documenta cómo restaurarlo.
  4. Dados los entornos de desarrollo y pruebas, cuando se cargan datos, entonces nunca incluyen datos personales reales sin anonimizar.

# E1 - Seguridad y acceso

### HU-003 Iniciar y cerrar sesión

- **Actor:** Operativo
- **Descripción:** Como usuario, quiero iniciar sesión con mi cuenta y cerrar sesión, para que solo las personas autorizadas accedan a los datos de Big Media.
- **Prioridad:** Must
- **Complejidad:** M
- **Precondición:** El usuario fue dado de alta por un administrador (HU-005).
- **Regla de negocio:** No existe registro público: solo el administrador crea cuentas. Las contraseñas se almacenan cifradas con un algoritmo de hash seguro, nunca en texto plano. La sesión expira tras un período de inactividad definido.
- **Criterios de aceptación:**
  1. Dadas credenciales válidas, cuando el usuario ingresa, entonces accede a las secciones permitidas por su rol.
  2. Dadas credenciales inválidas, cuando intenta ingresar, entonces ve un mensaje genérico que no revela si el usuario existe.
  3. Dados varios intentos fallidos seguidos, cuando se supera el límite, entonces la cuenta se bloquea temporalmente.
  4. Dada una sesión inactiva más allá del límite, cuando el usuario actúa, entonces se le pide ingresar de nuevo.

### HU-004 Roles y permisos

- **Actor:** Administrador
- **Descripción:** Como administrador, quiero asignar a cada usuario un rol (Operativo, Administrador o Lectura), para que cada persona tenga solo los permisos que necesita.
- **Prioridad:** Must
- **Complejidad:** M
- **Precondición:** HU-003 completa.
- **Regla de negocio:** Operativo: crea y edita campañas, reservas, clientes, marcas, interacciones y costos, y administra carteles. Administrador: todo, incluida la configuración y la gestión de usuarios. Lectura: solo consulta y reportes. Gerencia no es un rol: es un permiso aparte para ver ingresos y auditoría (HU-052, HU-007) que se suma a cualquier rol. Los permisos se verifican siempre en el servidor, no solo ocultando botones en pantalla.
- **Criterios de aceptación:**
  1. Dado un usuario Operativo, cuando intenta una acción de administración (configuración o usuarios), entonces el servidor la rechaza.
  2. Dado un usuario de Lectura, cuando intenta crear o editar un registro, entonces el servidor lo rechaza aunque envíe la petición por otra vía.
  3. Dado un usuario, cuando cambia su rol, entonces el cambio rige desde su próxima petición.

### HU-005 Gestionar usuarios

- **Actor:** Administrador
- **Descripción:** Como administrador, quiero crear, editar e inactivar usuarios y restablecer contraseñas, para controlar quién usa el sistema.
- **Prioridad:** Must
- **Complejidad:** S
- **Precondición:** HU-004 completa.
- **Regla de negocio:** Un usuario inactivo no puede ingresar pero conserva su historial de acciones. No se pueden eliminar usuarios con actividad registrada. Debe existir siempre al menos un administrador activo.
- **Criterios de aceptación:**
  1. Dado un usuario nuevo, cuando se crea con nombre, correo y rol, entonces recibe una forma segura de definir su contraseña.
  2. Dado un usuario inactivado, cuando intenta ingresar, entonces el acceso es rechazado y sus registros pasados se conservan.
  3. Dado el único administrador activo, cuando se intenta inactivarlo o cambiarle el rol, entonces el sistema lo impide.

### HU-006 Baja lógica en todo el sistema

- **Actor:** Sistema
- **Descripción:** Como gerencia, quiero que ningún registro de negocio se borre físicamente en la operación diaria, para conservar el historial completo.
- **Prioridad:** Must
- **Complejidad:** S
- **Precondición:** HU-004 completa.
- **Regla de negocio:** Proveedores, formatos, carteles, clientes y marcas se inactivan. Las reservas y campañas se cancelan. Las reservas, campañas y costos no tienen acción de eliminar para el rol Operativo. Un registro inactivo no se ofrece en las listas de selección nuevas, pero se sigue mostrando donde ya estaba asociado.
- **Criterios de aceptación:**
  1. Dado cualquier entidad de negocio, cuando un operativo busca una acción de eliminar, entonces no existe en la interfaz ni en la API.
  2. Dado un registro inactivo, cuando se crea una reserva o campaña nueva, entonces no aparece como opción.
  3. Dado un registro inactivo con reservas pasadas, cuando se consulta un reporte histórico, entonces sigue incluido.
  4. Dado un administrador que corrige una carga errónea sin actividad asociada, cuando elimina, entonces la acción queda auditada.

### HU-007 Auditoría de cambios

- **Actor:** Gerencia
- **Descripción:** Como gerencia, quiero consultar quién cambió qué y cuándo en reservas, campañas, tarifas y configuración, para resolver cualquier discusión del tipo "yo nunca cambié esa fecha".
- **Prioridad:** Should
- **Complejidad:** M
- **Precondición:** HU-003 completa.
- **Regla de negocio:** Se audita como mínimo, en Reserva: fechas de inicio y fin, estado, cartel y los tres precios. También cambios de estado de campaña, cambios de tarifa de lista de un cartel y cambios de configuración. El registro de auditoría no se puede editar ni borrar desde la aplicación.
- **Criterios de aceptación:**
  1. Dada una reserva con cambios, cuando se abre su historial, entonces se ve usuario, fecha y hora, valor anterior y valor nuevo de cada campo.
  2. Dado un cambio hecho por un proceso automático o una importación, cuando ocurre, entonces queda auditado con el origen.
  3. Dado un usuario de cualquier rol, cuando intenta modificar un registro de auditoría, entonces el sistema lo impide.

# E2 - Inventario de soportes

### HU-008 Gestionar proveedores

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero crear, editar e inactivar proveedores con nombre y servicio, para asociarlos a carteles y a costos.
- **Prioridad:** Must
- **Complejidad:** S
- **Precondición:** Sesión iniciada con rol Operativo o superior.
- **Regla de negocio:** El nombre del proveedor es obligatorio y único. Un proveedor inactivo no se ofrece en selecciones nuevas, pero se conserva en los carteles y costos ya asociados.
- **Criterios de aceptación:**
  1. Dado un proveedor nuevo con nombre, cuando se guarda, entonces queda disponible para asociarlo a carteles y costos.
  2. Dado un nombre ya existente, cuando se intenta guardar, entonces el sistema lo rechaza.
  3. Dado un proveedor inactivo, cuando se edita un cartel, entonces no aparece como opción nueva.

### HU-009 Gestionar formatos

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero administrar el catálogo de formatos con su modalidad, capacidad por defecto y dimensiones, para clasificar cada cartel.
- **Prioridad:** Must
- **Complejidad:** S
- **Precondición:** Sesión iniciada con rol Operativo o superior.
- **Regla de negocio:** Hay 7 formatos: PPL o Gran Formato, Banderolas, Séxtuples, LED, Mediano Formato, Monocolumnas y Carteleras. La modalidad es fija o digital y vive solo en el formato, no se repite en el cartel. "Fija" no implica capacidad 1: los séxtuples son fijos pero multi-marca, con cantidad de slots variable por ubicación. Un formato no tiene un tamaño fijo: ancho y alto son opcionales, como medida de referencia, y el tamaño real se carga en cada cartel (RN-019).
- **Criterios de aceptación:**
  1. Dado un formato nuevo, cuando se guarda con nombre, modalidad y capacidad por defecto mayor o igual a 1, entonces queda disponible para crear carteles.
  2. Dada una capacidad por defecto menor a 1, cuando se guarda, entonces se rechaza.
  3. Dado un formato inactivo, cuando se crea un cartel, entonces no aparece como opción.

### HU-010 Gestionar carteles

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero dar de alta y editar carteles con formato, dirección, tamaño o cantidad de slots, tarifa de lista, zona, proveedor y foto, para tener el inventario real administrable.
- **Prioridad:** Must
- **Complejidad:** M
- **Precondición:** HU-008, HU-009 y HU-013 completas.
- **Regla de negocio:** Big Media identifica un cartel por Dirección + Tamaño (gran formato) o Dirección + cantidad de slots (séxtuples); no existe un código de cartel con significado de negocio. El sistema genera un identificador interno y muestra el cartel siempre con su nombre legible compuesto. La foto se guarda como enlace a un almacenamiento de archivos externo.
- **Criterios de aceptación:**
  1. Dado un cartel, cuando aparece en una lista, selector o mensaje, entonces se muestra con Dirección y Tamaño o Slots, nunca con un identificador interno.
  2. Dado un cartel nuevo sin formato, dirección o zona, cuando se guarda, entonces se rechaza indicando qué falta.
  3. Dada una foto cargada, cuando se abre el cartel, entonces se puede ver desde la ficha.
  4. Dada la tarifa de lista, cuando se modifica, entonces las reservas ya guardadas no cambian de precio (ver HU-029).

### HU-011 Capacidad del cartel precargada y editable

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero que al elegir el formato la capacidad del cartel se complete con la capacidad por defecto pero poder cambiarla, para reflejar LED con loops distintos y séxtuples con slots variables.
- **Prioridad:** Must
- **Complejidad:** S
- **Precondición:** HU-009 y HU-010 en construcción.
- **Regla de negocio:** La validación de disponibilidad usa la capacidad guardada en el cartel, no la del formato. Reducir la capacidad por debajo de los cupos ya reservados en fechas futuras requiere confirmación explícita y queda auditado.
- **Criterios de aceptación:**
  1. Dado un cartel nuevo, cuando se elige el formato, entonces la capacidad toma la capacidad por defecto y puede editarse.
  2. Dado un cartel existente, cuando se cambia su formato, entonces la capacidad no se pisa sin confirmación.
  3. Dado un cartel con capacidad reducida bajo sus cupos reservados a futuro, cuando se guarda, entonces el sistema advierte los conflictos y pide confirmar.

### HU-012 Estados del cartel

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero marcar un cartel como activo, en mantenimiento, de baja, apagado o con vidrio destruido, para reflejar su situación real sin borrarlo.
- **Prioridad:** Should
- **Complejidad:** S
- **Precondición:** HU-010 completa. Pendiente la lista completa de estados físicos que confirme Seba.
- **Regla de negocio:** "Ocupado" no es un estado del cartel: se calcula desde las reservas (HU-040). La lista de estados es configurable por el administrador para sumar casos nuevos sin tocar código. Un cartel de baja sale de las vistas operativas pero se conserva.
- **Criterios de aceptación:**
  1. Dada la lista de estados, cuando se despliega, entonces incluye al menos Activo, En mantenimiento, De baja, Apagado y Vidrio destruido.
  2. Dado un cartel de baja, cuando el operativo abre las listas operativas, entonces no aparece, pero sigue disponible en reportes históricos.
  3. Dado un cartel que pasa a un estado no operativo con reservas activas, cuando se guarda, entonces se aplica HU-039.

### HU-013 Zona por departamento

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero clasificar cada cartel por zona o departamento, para filtrar el inventario y los reportes.
- **Prioridad:** Should
- **Complejidad:** S
- **Precondición:** Listado de los 9 departamentos de Mendoza confirmado por Seba.
- **Regla de negocio:** El relevamiento habla de 9 departamentos. La lista de zonas es administrable para sumar un décimo sin tocar código.
- **Criterios de aceptación:**
  1. Dada la lista de zonas, cuando se despliega, entonces muestra los departamentos confirmados.
  2. Dado un cartel con zona, cuando se filtra el inventario por ella, entonces aparece.
  3. Dada una zona nueva agregada por el administrador, cuando se abre un cartel, entonces ya se puede elegir.

### HU-014 Buscar y filtrar el inventario

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero listar el inventario con filtros por zona, formato, modalidad, estado y texto de dirección, y ordenarlo, para encontrar un cartel rápido.
- **Prioridad:** Must
- **Complejidad:** M
- **Precondición:** HU-010 completa.
- **Regla de negocio:** Las listas operativas excluyen carteles de baja por defecto, con opción de incluirlos. El inventario real ronda los cientos de carteles y la lista debe seguir siendo fluida.
- **Criterios de aceptación:**
  1. Dados uno o más filtros, cuando se aplican, entonces la lista muestra solo los carteles que cumplen todos.
  2. Dado un texto parcial de dirección, cuando se busca, entonces devuelve las coincidencias sin distinguir mayúsculas ni tildes.
  3. Dado el inventario real completo, cuando se abre la lista, entonces responde en menos de 2 segundos.

### HU-015 Importar inventario desde planillas

- **Actor:** Administrador
- **Descripción:** Como administrador, quiero importar el relevamiento de carteles desde archivos CSV con un reporte de errores, para arrancar el sistema con el inventario real cargado.
- **Prioridad:** Must
- **Complejidad:** L
- **Precondición:** HU-009, HU-010 y HU-013 completas. Las planillas de Gran Formato (66 o más posiciones) y Séxtuples (226 posiciones) ya existen pero en formato visual y deben transformarse a CSV tabular.
- **Regla de negocio:** Banderolas, Mediano Formato, Monocolumnas y Carteleras todavía no tienen relevamiento cuantitativo y no se cargan hasta que exista. En los séxtuples la capacidad es la cantidad de slots relevada. La importación no duplica carteles que ya existen (misma dirección y tamaño o slots).
- **Criterios de aceptación:**
  1. Dado un CSV válido de Gran Formato, cuando se importa, entonces se crean todas sus posiciones con formato, dirección, tamaño y zona.
  2. Dado el CSV de Séxtuples, cuando se importa, entonces cada cartel queda con capacidad igual a sus slots.
  3. Dado un archivo con filas inválidas o duplicadas, cuando termina la importación, entonces un reporte lista cada fila rechazada con el motivo y las válidas se cargan igual.
  4. Dada una importación completa, cuando se ejecuta dos veces, entonces la segunda no crea duplicados.

# E3 - Clientes, marcas y CRM

### HU-016 Gestionar clientes

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero administrar clientes con nombre, razón social, CUIT, teléfono, correo y tipo (directo, intermediario o intermediario formal), para saber a quién se factura. Ningún dato es obligatorio para guardar un cliente: se completan a medida que se conocen.
- **Prioridad:** Must
- **Complejidad:** S
- **Precondición:** Sesión iniciada con rol Operativo o superior.
- **Regla de negocio:** El cliente es quien paga y lleva los datos de facturación. Su CUIT se precarga en los ítems a facturar (HU-060), donde puede cambiarse por ítem. Solo el cliente de tipo intermediario formal puede tener varios contactos (HU-068); los demás tipos usan los datos de contacto del propio cliente. En la interfaz se muestra por su nombre; si no tiene, como «Cliente sin nombre #id». Un cliente con marcas no se puede eliminar; se inactiva.
- **Criterios de aceptación:**
  1. Dado un cliente nuevo, con o sin datos cargados, cuando se guarda, entonces queda disponible para asociarle marcas.
  2. Dado un cliente inactivo, cuando se crea una marca nueva, entonces no aparece como opción.
  3. Dada una búsqueda por nombre o razón social, cuando se escribe parte del texto, entonces encuentra al cliente.

### HU-017 Gestionar marcas

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero administrar marcas (anunciantes) con rubro, cliente que factura y estado, para distinguir quién se anuncia de quién paga.
- **Prioridad:** Must
- **Complejidad:** M
- **Precondición:** HU-016 completa.
- **Regla de negocio:** La marca no tiene datos de facturación y no se le puede facturar. El cliente de la marca es obligatorio, sea cual sea la vía de entrada (pantalla, importación o API). El rubro vive en la marca, no en el cliente, porque el cliente suele ser una agencia. El grupo económico (por ejemplo, un grupo con varias marcas) es opcional: cada marca pertenece a lo sumo a uno, sin importar el cliente que factura (RN-016).
- **Criterios de aceptación:**
  1. Dada una marca nueva sin cliente, cuando se guarda por cualquier vía, entonces se rechaza.
  2. Dado un cliente intermediario, cuando se abre su ficha, entonces se listan todas sus marcas.
  3. Dada una marca con campañas, cuando se intenta eliminar, entonces el sistema lo impide y ofrece inactivarla.

### HU-018 Crear la marca homónima de un cliente directo

- **Actor:** Sistema
- **Descripción:** Como operativo, quiero que al crear un cliente de tipo directo se cree automáticamente una marca con el mismo nombre, para no cargarla a mano.
- **Prioridad:** Should
- **Complejidad:** S
- **Precondición:** HU-016 y HU-017 completas.
- **Regla de negocio:** Un cliente directo existe dos veces: como entidad legal a la que se factura y como marca impresa en el cartel, con la marca apuntando al mismo cliente. Si después el cliente cambia de razón social o de nombre, la marca no se toca: es lo que va en el cartel, y si hace falta se renombra a mano en Marcas (RN-017). Un cliente directo sin nombre no genera marca, porque no hay con qué nombrarla.
- **Criterios de aceptación:**
  1. Dado un cliente directo nuevo, cuando se guarda, entonces se crea en la misma operación una marca con su nombre asociada a él.
  2. Dado un cliente intermediario o intermediario formal, cuando se guarda, entonces no se crea ninguna marca.
  3. Dado un cliente directo ya existente, cuando se edita, entonces no se duplica la marca.
  4. Dado un fallo al crear la marca, cuando ocurre, entonces el cliente tampoco se crea, para no dejar datos a medias.
  5. Dado un cliente directo nuevo sin nombre, cuando se guarda, entonces no se crea ninguna marca.

### HU-019 Detectar marcas duplicadas

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero que el sistema me avise si cargo una marca con nombre igual o muy parecido a otra, para no fragmentar el análisis por marca.
- **Prioridad:** Should
- **Complejidad:** S
- **Precondición:** HU-017 completa.
- **Regla de negocio:** Con clientes directos la cantidad de marcas se parece a la de clientes, lo que aumenta el riesgo de duplicar por un error de tipeo. La comparación ignora mayúsculas, tildes y espacios de más.
- **Criterios de aceptación:**
  1. Dado un nombre igual o casi igual a uno existente, cuando se guarda, entonces el sistema muestra el aviso con la marca coincidente.
  2. Dado el aviso, cuando el operativo confirma que es otra marca, entonces puede guardar.
  3. Dada una importación, cuando hay posibles duplicados, entonces se informan en el reporte.

### HU-020 Registrar interacciones comerciales

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero registrar reuniones y llamadas con asunto, fecha, notas, cliente y campaña opcional, para no perder el rastro de las conversaciones comerciales.
- **Prioridad:** Should
- **Complejidad:** S
- **Precondición:** HU-016 completa.
- **Regla de negocio:** El asunto, la fecha y el cliente son obligatorios. La campaña es opcional. Si el cliente es un intermediario formal, se puede indicar opcionalmente con cuál de sus contactos fue (HU-068). También se puede indicar opcionalmente la marca, para las conversaciones que ocurren antes de que exista una campaña: tiene que ser una marca del cliente y, si además hay campaña, la campaña tiene que ser de esa marca (RN-018).
- **Criterios de aceptación:**
  1. Dada una interacción sin asunto, cuando se guarda, entonces se rechaza.
  2. Dada una interacción con cliente y campaña, cuando se guarda, entonces aparece en la ficha de ambos.
  3. Dada la lista de interacciones, cuando se abre, entonces se ordena por fecha descendente.
  4. Dada una interacción con marca y sin campaña, cuando se guarda, entonces aparece en la ficha del cliente y en la de la marca (RN-018).
  5. Dada una interacción con una marca de otro cliente, o con una campaña de otra marca, cuando se guarda, entonces se rechaza (RN-018).

### HU-021 Ficha de cliente

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero ver desde la ficha de un cliente sus marcas, las campañas que factura y su historial de interacciones, para tener el contexto completo antes de llamarlo.
- **Prioridad:** Should
- **Complejidad:** M
- **Precondición:** HU-017, HU-020 y HU-023 completas.
- **Regla de negocio:** El cliente que factura una campaña se deduce de su marca. Si una marca cambia de intermediario, el histórico se reasigna salvo que se use HU-027.
- **Criterios de aceptación:**
  1. Dada la ficha de una agencia, cuando se abre, entonces se ven sus marcas y las campañas asociadas.
  2. Dada la misma ficha, cuando se baja a interacciones, entonces se ve el historial por fecha.
  3. Dado un cliente sin campañas, cuando se abre, entonces las secciones aparecen vacías sin errores.

### HU-022 Ficha de marca

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero ver desde la ficha de una marca todas sus campañas sin importar qué agencia las pagó, para entender su actividad total.
- **Prioridad:** Should
- **Complejidad:** S
- **Precondición:** HU-017 y HU-023 completas.
- **Regla de negocio:** Las campañas de una marca se listan aunque el pagador haya sido distinto en distintos momentos.
- **Criterios de aceptación:**
  1. Dada la ficha de una marca, cuando se abre, entonces se ven todas sus campañas con su estado.
  2. Dada una marca de un grupo económico, cuando se abre su ficha, entonces se ven las otras marcas del mismo grupo (RN-016).

### HU-068 Gestionar varios contactos de un intermediario formal

- **Actor:** Operativo
- **Descripción:** Como operador comercial, quiero cargar varios contactos en un cliente de tipo intermediario formal, para saber con quién hablar en cada agencia o central de medios.
- **Prioridad:** Should
- **Complejidad:** M
- **Precondición:** HU-016 completa.
- **Regla de negocio:** Hay tres tipos de cliente: directo, intermediario e intermediario formal. Solo el intermediario formal puede tener varios contactos. Cada contacto lleva nombre (obligatorio), cargo o área, correo, teléfono y notas, y no lleva datos de facturación, que siguen en el cliente. Un cliente tiene como máximo un contacto principal. Los contactos no se borran: se inactivan (HU-006). Si un cliente deja de ser intermediario formal, primero se inactivan sus contactos.
- **Criterios de aceptación:**
  1. Dado un cliente de tipo intermediario formal, cuando el operativo abre su ficha, entonces puede agregar dos o más contactos.
  2. Dado un cliente directo o intermediario, cuando se abre su ficha, entonces no se ofrece la carga de contactos múltiples.
  3. Dado un contacto marcado como principal, cuando se marca otro, entonces el anterior deja de ser principal.
  4. Dado un contacto sin nombre, cuando se guarda, entonces se rechaza.
  5. Dado un contacto inactivado, cuando se elige un contacto en una interacción, entonces no aparece como opción, pero se conserva en las interacciones pasadas.
  6. Dado un cliente intermediario formal con contactos activos, cuando se intenta cambiar su tipo, entonces el sistema pide inactivar antes los contactos.
  7. Dada la ficha de un intermediario formal (HU-021), cuando se abre, entonces se ven sus contactos y, en cada interacción, el contacto indicado si lo hubo.

# E4 - Campañas

### HU-023 Crear campaña

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero crear una campaña con los datos que tenga en el momento, para agrupar las reservas bajo una unidad comercial y completarla después.
- **Prioridad:** Must
- **Complejidad:** M
- **Precondición:** HU-017 completa.
- **Regla de negocio:** Ningún campo de la campaña es obligatorio para guardarla: nombre, cliente que factura, marca anunciante y fechas planificadas se completan después y se exigen recién al confirmarla (HU-059). Las fechas de la campaña son intención comercial y valor por defecto para sus reservas; la fuente de verdad del solapamiento es la fecha de cada reserva (HU-025). El cliente que factura se deduce de la marca (ver supuestos). Si la marca no existe, se puede crear sin salir de la pantalla de campaña.
- **Criterios de aceptación:**
  1. Dada una campaña sin ningún dato cargado, cuando se guarda, entonces se guarda igual.
  2. Dada una campaña con marca, cuando se guarda, entonces se muestra el cliente que factura.
  3. Dada la pantalla de campaña, cuando el operativo necesita una marca inexistente, entonces puede crearla en el momento y queda seleccionada.
  4. Dada una campaña, cuando se abre, entonces se ve la lista de sus reservas con un acceso directo para agregar una nueva.

### HU-024 Estados de campaña

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero mover la campaña entre cotizada, confirmada, cancelada y perdida, para reflejar su situación comercial.
- **Prioridad:** Must
- **Complejidad:** S
- **Precondición:** HU-023 completa.
- **Regla de negocio:** "Perdida" es una cotización que nunca cerró (nunca fue plata real); "cancelada" es una confirmada que se cayó y quizás facturó seña. Se distinguen por defecto hasta que Seba responda la pregunta 6. "Campaña activa" significa estado Confirmada, sin filtrar por fecha: mide compromiso comercial, no ocupación del día. Para pasar a Confirmada se exigen cliente que factura, marca y fechas (HU-059).
- **Criterios de aceptación:**
  1. Dado el selector de estado, cuando se despliega, entonces ofrece los cuatro valores.
  2. Dado un panel que cuenta campañas activas, cuando se calcula, entonces cuenta las Confirmadas sin importar sus fechas.
  3. Dada una campaña cancelada o perdida, cuando se consulta, entonces sigue visible en el histórico.

### HU-025 Monto y cantidad de reservas de la campaña

- **Actor:** Sistema
- **Descripción:** Como operativo, quiero ver en la campaña el monto total y la cantidad de reservas, calculados desde sus reservas, para no cargarlos a mano.
- **Prioridad:** Should
- **Complejidad:** S
- **Precondición:** HU-028 completa.
- **Regla de negocio:** El monto es la suma del total de sus reservas y la cantidad es su conteo. Las fechas de la campaña no se derivan de las reservas: son fechas planificadas que carga el operativo. Las reservas canceladas no se suman. Son valores de solo lectura y se muestran actualizados al momento, sin esperar un recálculo.
- **Criterios de aceptación:**
  1. Dada una campaña con tres reservas activas, cuando se abre, entonces muestra el monto total y la cantidad de reservas correctos.
  2. Dada una reserva que se cancela, cuando se vuelve a abrir la campaña, entonces ya no se suma.
  3. Dado un operativo, cuando abre la campaña, entonces no puede editar esos valores.

### HU-026 Confirmar campaña y sus reservas (fusionada en HU-059)

Esta historia se fusionó en HU-059: la confirmación en bloque es parcial (las reservas sin conflicto pasan a Confirmada y las conflictivas quedan Pendientes) y no atómica como se proponía acá. Se conserva el número para no renumerar el resto.

### HU-027 Fijar el cliente que factura de una campaña

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero poder indicar un cliente de facturación propio en una campaña, para no reescribir el histórico cuando una marca cambia de intermediario o se compra por dos vías.
- **Prioridad:** Could
- **Complejidad:** M
- **Precondición:** HU-023 completa. Respuesta de Seba a las preguntas 14 y 15; si ambas son "nunca", la historia se descarta.
- **Regla de negocio:** El cliente propio es opcional: vacío se comporta como la deducción desde la marca; con valor, la reemplaza. Antes de cambiar el cliente de una marca, el sistema estampa el cliente anterior en las campañas existentes.
- **Criterios de aceptación:**
  1. Dada una campaña sin cliente propio, cuando se consulta quién factura, entonces es el cliente de la marca.
  2. Dada una campaña con cliente propio, cuando se consulta, entonces es el indicado.
  3. Dado un cambio de cliente en una marca, cuando se guarda, entonces las campañas anteriores conservan su cliente original.

# E5 - Reservas y motor de disponibilidad

### HU-028 Crear y editar reservas

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero reservar un cartel para una campaña indicando fecha de inicio, fecha de fin y estado, para bloquear su disponibilidad.
- **Prioridad:** Must
- **Complejidad:** M
- **Precondición:** HU-010 y HU-023 completas.
- **Regla de negocio:** La reserva es la intersección entre Campaña y Cartel y lleva sus propias fechas (nunca en la campaña). Cartel, fecha de inicio y fecha de fin son obligatorios siempre: no hay contratos abiertos. La fecha de fin no puede ser anterior a la de inicio. Una reserva bloquea cupo en las vistas de disponibilidad desde que tiene fecha de inicio y su estado no es Cancelada; Pendiente y Confirmada bloquean igual visualmente.
- **Criterios de aceptación:**
  1. Dada una reserva sin cartel, sin fecha de inicio o sin fecha de fin, cuando se guarda por cualquier vía, entonces se rechaza.
  2. Dada una fecha de fin anterior a la de inicio, cuando se guarda, entonces se rechaza con un mensaje claro.
  3. Dado un cartel inactivo o de baja, cuando se intenta reservar, entonces se rechaza (ver HU-039).
  4. Dada una campaña, cuando el operativo agrega una reserva desde ella, entonces la campaña ya viene seleccionada.

### HU-029 Precio de alquiler precargado y estampado

- **Actor:** Sistema
- **Descripción:** Como operativo, quiero que al elegir el cartel se precargue el precio de alquiler desde su tarifa de lista, editable, y que quede fijo al guardar, para que la rentabilidad histórica no cambie cuando suben las tarifas.
- **Prioridad:** Must
- **Complejidad:** S
- **Precondición:** HU-010 y HU-028 completas.
- **Regla de negocio:** El precio se guarda en la reserva y no se lee en vivo del cartel. Los precios de impresión y fijación se cargan a mano. El total de la reserva es la suma de los tres precios y se calcula siempre, no se tipea.
- **Criterios de aceptación:**
  1. Dada una reserva nueva, cuando se elige el cartel, entonces el precio de alquiler toma su tarifa de lista y puede editarse.
  2. Dada una reserva guardada, cuando cambia la tarifa de lista del cartel, entonces el precio de la reserva no cambia.
  3. Dados los tres precios, cuando se guarda, entonces el total es su suma exacta.
  4. Dado un precio negativo, cuando se guarda, entonces se rechaza.

### HU-030 Nombre legible de la reserva

- **Actor:** Sistema
- **Descripción:** Como operativo, quiero que cada reserva se identifique con un nombre generado automáticamente, para reconocerla en listas y mensajes sin abrirla.
- **Prioridad:** Should
- **Complejidad:** S
- **Precondición:** HU-028 completa.
- **Regla de negocio:** El nombre sigue el patrón Marca, Cartel y mes y año (por ejemplo "McDonald's - Av. San Martín 1234 6x3 - Ago 2026"). La marca sale de la campaña, no del cliente; si la campaña aún no tiene marca, se usa "Sin marca" y el nombre se corrige solo cuando se cargue. El cartel se referencia con su nombre legible, no con un código interno. Es de solo lectura.
- **Criterios de aceptación:**
  1. Dada una reserva nueva, cuando se guarda, entonces el nombre se genera sin intervención del operativo.
  2. Dada una reserva cuya marca, cartel o fecha cambian, cuando se guarda, entonces el nombre se actualiza.
  3. Dada cualquier lista de reservas, cuando se muestra, entonces ninguna aparece sin nombre.

### HU-031 Validar solapamiento al confirmar una reserva

- **Actor:** Sistema
- **Descripción:** Como operativo, quiero que el sistema impida confirmar una reserva si el cartel ya no tiene cupo libre en esas fechas, para evitar la doble reserva.
- **Prioridad:** Must
- **Complejidad:** XL
- **Precondición:** HU-011 y HU-028 completas.
- **Regla de negocio:** Es el objetivo central del proyecto y se valida siempre en el servidor, dentro de la misma operación que guarda la reserva, de modo que ninguna vía de entrada (pantalla, importación o API) pueda saltearla. La validación dura corre al pasar la reserva a Confirmada y cada vez que se edita una Confirmada (fechas, cartel o estado); no corre en Pendiente. Una reserva Cancelada libera el cupo y no valida. Se cuentan las reservas del mismo cartel, excluyendo la actual, que se solapen con el rango y cuyo estado ocupe cupo; si esa cantidad es igual o mayor a la capacidad del cartel, se bloquea.
- **Criterios de aceptación:**
  1. Dado un cartel de capacidad 1 con una reserva confirmada, cuando se confirma otra con rango idéntico, contenido, contenedor o con solapamiento parcial por izquierda o derecha, entonces se bloquea.
  2. Dado un cartel digital con 12 de 20 cupos ocupados, cuando se confirma otra reserva, entonces se permite; con 20 de 20, se bloquea.
  3. Dadas dos reservas separadas por un día, cuando se confirman, entonces se permite.
  4. Dado un conflicto solo con una reserva cancelada, cuando se confirma, entonces se permite.
  5. Dada una edición que solo cambia un precio, cuando se guarda, entonces no se revalida; si cambia fechas, cartel o estado, sí.
  6. Dada una reserva que se pasa a Cancelada, cuando se guarda, entonces siempre se permite.
  7. Dada una prueba automatizada con los 16 casos de la matriz de disponibilidad (ver el anexo de supuestos), cuando corre, entonces todos pasan.

### HU-032 Mensaje de conflicto que nombra las reservas

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero que el error de disponibilidad me diga qué cartel está lleno, entre qué fechas y con qué reservas en conflicto, para saber a quién llamar.
- **Prioridad:** Must
- **Complejidad:** S
- **Precondición:** HU-031 en construcción.
- **Regla de negocio:** El mensaje nunca es genérico ni técnico. Indica cartel, cupos ocupados sobre capacidad, rango de fechas y nombres de las reservas que chocan.
- **Criterios de aceptación:**
  1. Dado un conflicto de cupo, cuando se bloquea, entonces el mensaje incluye cartel, cupos ocupados de la capacidad, fechas y reservas en conflicto.
  2. Dado un mensaje de error, cuando se lee, entonces no contiene códigos internos ni términos técnicos.

### HU-033 Reglas de borde y tentativa configurables

- **Actor:** Sistema
- **Descripción:** Como administrador, quiero que el criterio del día de borde y el tratamiento de las reservas tentativas salgan de la configuración, para adaptarlo a lo que defina Seba sin cambiar código.
- **Prioridad:** Should
- **Complejidad:** S
- **Precondición:** HU-001 y HU-031 completas.
- **Regla de negocio:** Con borde inclusivo el día 15 se pisa; con exclusivo, no. La tentativa siempre ocupa cupo visualmente; que también cuente para el bloqueo duro depende del parámetro.
- **Criterios de aceptación:**
  1. Dado el borde inclusivo, cuando una reserva termina el 15 y otra empieza el 15 en un cartel de capacidad 1, entonces se bloquea; con exclusivo, se permite.
  2. Dado que la tentativa no cuenta para el bloqueo, cuando existe solo una tentativa en el rango, entonces no impide confirmar otra reserva.
  3. Dado un cambio de configuración, cuando se valida de nuevo, entonces aplica el valor nuevo.

### HU-034 Garantía ante reservas simultáneas

- **Actor:** Sistema
- **Descripción:** Como gerencia, quiero que dos personas que reservan a la vez el último cupo de un cartel no puedan quedar ambas confirmadas, para que la doble reserva sea imposible y no solo improbable.
- **Prioridad:** Must
- **Complejidad:** L
- **Precondición:** HU-031 completa.
- **Regla de negocio:** La verificación de cupo y el guardado de la reserva ocurren de forma atómica por cartel: las operaciones concurrentes sobre el mismo cartel se serializan mediante bloqueo o transacción con aislamiento adecuado. Operaciones sobre carteles distintos no se bloquean entre sí.
- **Criterios de aceptación:**
  1. Dado un cartel con un cupo libre, cuando dos confirmaciones llegan en paralelo, entonces una se acepta y la otra se rechaza con el mensaje de conflicto.
  2. Dada una prueba automatizada con al menos 50 confirmaciones concurrentes sobre un cartel de capacidad 20, cuando termina, entonces nunca hay más de 20 reservas superpuestas.
  3. Dadas confirmaciones simultáneas sobre carteles distintos, cuando se procesan, entonces no se demoran entre sí de forma perceptible.

### HU-035 Ciclo de vida de la reserva

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero mover la reserva entre pendiente, confirmada, finalizada y cancelada solo por transiciones válidas, para no dejar datos incoherentes.
- **Prioridad:** Must
- **Complejidad:** M
- **Precondición:** HU-031 completa.
- **Regla de negocio:** Transiciones válidas: pendiente a confirmada o cancelada; confirmada a finalizada o cancelada. Una cancelada solo vuelve a confirmada revalidando el cupo. Una finalizada no vuelve a un estado activo. Si una confirmada se reprograma o se cancela y recrea es una decisión abierta (pregunta 10).
- **Criterios de aceptación:**
  1. Dada una reserva cancelada, cuando se intenta confirmar, entonces se ejecuta la validación de solapamiento antes de permitirlo.
  2. Dada una reserva finalizada, cuando se intenta reactivar, entonces el sistema lo impide.
  3. Dada una transición inválida, cuando se intenta por cualquier vía, entonces se rechaza con un mensaje claro.

### HU-036 Finalizar reservas vencidas automáticamente

- **Actor:** Sistema
- **Descripción:** Como operativo, quiero que las reservas cuya fecha de fin ya pasó se marquen como finalizadas solas, para mantener el estado al día sin tareas manuales.
- **Prioridad:** Should
- **Complejidad:** S
- **Precondición:** HU-035 completa.
- **Regla de negocio:** Una tarea programada diaria, de madrugada en horario de Argentina, pasa a Finalizada las reservas confirmadas cuya fecha de fin es anterior a hoy.
- **Criterios de aceptación:**
  1. Dada una reserva confirmada con fecha de fin de ayer, cuando corre la tarea, entonces pasa a Finalizada.
  2. Dada una reserva pendiente o cancelada, cuando corre la tarea, entonces no cambia.
  3. Dado un fallo de la tarea, cuando ocurre, entonces queda registrado, se notifica al administrador y se reintenta en la próxima corrida.
  4. Dada una tarea ejecutada dos veces el mismo día, cuando termina, entonces el resultado es el mismo.

### HU-037 Cancelar sin borrar y liberar cupo

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero cancelar una reserva sin eliminarla y que el cupo quede libre, para poder reservar de nuevo ese cartel en el mismo rango.
- **Prioridad:** Must
- **Complejidad:** S
- **Precondición:** HU-035 completa.
- **Regla de negocio:** Cancelar cambia el estado, nunca borra, y conserva el historial. Cancelar siempre se permite.
- **Criterios de aceptación:**
  1. Dada una reserva confirmada, cuando se cancela, entonces el registro persiste con estado Cancelada.
  2. Dado el cupo recién liberado, cuando se crea otra reserva en el mismo rango, entonces se permite.
  3. Dado un operativo, cuando mira la reserva, entonces no existe una acción de eliminar.

### HU-038 Cargar reservas con fechas pasadas

- **Actor:** Administrador
- **Descripción:** Como administrador, quiero importar reservas históricas con fechas pasadas, para tener la historia que alimenta los reportes.
- **Prioridad:** Could
- **Complejidad:** M
- **Precondición:** HU-031 completa. Respuesta de Seba a las preguntas 8 y 11 sobre fuente, volumen y calidad del dato.
- **Regla de negocio:** Las reservas históricas entran como Finalizadas. Si se permite crear a mano reservas con fecha pasada es una decisión abierta.
- **Criterios de aceptación:**
  1. Dado un archivo histórico válido, cuando se importa, entonces las reservas pasadas quedan Finalizadas y no consumen cupo futuro.
  2. Dado un archivo con filas inválidas, cuando termina, entonces el reporte indica cada fila rechazada y el motivo.
  3. Dado un operativo, cuando intenta crear a mano una reserva con fecha pasada, entonces se aplica la regla acordada.

### HU-039 Cartel fuera de servicio con reservas activas

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero que el sistema me avise cuando un cartel se rompe o se apaga y tiene reservas activas, para reubicar o avisar a los clientes.
- **Prioridad:** Should
- **Complejidad:** M
- **Precondición:** HU-012 y HU-028 completas. Respuesta de Seba a las preguntas 9 y 18.
- **Regla de negocio:** Hasta que Seba defina, el comportamiento por defecto es alertar y listar las reservas afectadas, sin modificarlas, y bloquear nuevas reservas sobre el cartel mientras no esté operativo.
- **Criterios de aceptación:**
  1. Dado un cartel con reservas activas, cuando pasa a un estado no operativo, entonces el sistema muestra cuáles son esas reservas.
  2. Dado un cartel no operativo, cuando se intenta una reserva nueva, entonces se rechaza con un mensaje claro.
  3. Dado un cartel que vuelve a Activo, cuando se intenta reservar, entonces se permite de nuevo.

### HU-040 Ocupación del cartel calculada al momento

- **Actor:** Sistema
- **Descripción:** Como operativo, quiero ver en cada cartel cuántas reservas activas tiene y si está libre u ocupado, siempre actualizado, para decidir sin esperar ningún recálculo.
- **Prioridad:** Must
- **Complejidad:** M
- **Precondición:** HU-028 completa.
- **Regla de negocio:** La ocupación nunca se guarda como dato manual ni diferido: se calcula en cada consulta desde las reservas, o se mantiene sincronizada dentro de la misma operación que modifica la reserva. Un cartel está ocupado hoy cuando los cupos ocupados vigentes alcanzan su capacidad; en multi-marca se muestra cupo usado sobre capacidad.
- **Criterios de aceptación:**
  1. Dada una reserva que se crea, confirma o cancela, cuando se consulta el cartel inmediatamente después, entonces el valor ya está actualizado.
  2. Dado un cambio hecho por una importación o la API, cuando ocurre, entonces el valor igualmente es correcto.
  3. Dado un cartel de capacidad 20 con 12 reservas vigentes, cuando se muestra, entonces indica 12 de 20.

# E6 - Vista de disponibilidad

### HU-041 Ver el estado actual de ocupación

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero una lista de carteles ordenada por estado de ocupación con accesos rápidos a Libres y Ocupados, para saber de un vistazo qué hay disponible hoy.
- **Prioridad:** Must
- **Complejidad:** S
- **Precondición:** HU-040 completa.
- **Regla de negocio:** Muestra el estado actual, no la proyección a futuro. Excluye los carteles de baja. Para multi-marca muestra cupo usado sobre capacidad.
- **Criterios de aceptación:**
  1. Dada la vista, cuando se abre, entonces lista los carteles ordenados por estado de ocupación.
  2. Dados los accesos rápidos, cuando se eligen Libres u Ocupados, entonces filtran correctamente.
  3. Dada la vista, cuando se combina con los filtros del inventario (zona, formato), entonces se respetan.

### HU-042 Calendario de disponibilidad a futuro

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero elegir un rango de fechas y una zona y ver qué carteles están libres en esas fechas, para responder "¿está libre en octubre?" sin abrir registros.
- **Prioridad:** Should
- **Complejidad:** L
- **Precondición:** HU-031 completa. Respuesta de Seba a la pregunta 20: si la vista actual le alcanza, baja a Could.
- **Regla de negocio:** Es la pantalla que el cliente pidió originalmente. Muestra carteles en filas y fechas en columnas (semanas o meses), con celdas coloreadas por ocupación. En multi-marca, la celda muestra cupos usados sobre capacidad (por ejemplo 12/20). El rango por defecto es de 3 meses, ampliable a 12.
- **Criterios de aceptación:**
  1. Dado el inventario real y una ventana de 12 meses, cuando se abre la pantalla, entonces carga en menos de 3 segundos.
  2. Dados rango, zona, formato y modalidad como filtros, cuando se aplican, entonces la grilla muestra solo los carteles correspondientes.
  3. Dada una celda ocupada, cuando se hace click, entonces muestra la campaña y la reserva que la ocupan.
  4. Dado un cartel de baja o no operativo, cuando se muestra la grilla, entonces aparece señalado o excluido según el filtro.

# E7 - Costos y rentabilidad

### HU-043 Registrar costos de una reserva

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero cargar líneas de costo (alquiler, impresión, fijación u otro) con proveedor, monto y fecha dentro de una reserva, para conocer lo que realmente costó.
- **Prioridad:** Should
- **Complejidad:** M
- **Precondición:** HU-028 y HU-008 completas.
- **Regla de negocio:** Cada costo pertenece a una reserva o a un ítem de facturación (HU-063): es el mismo registro y se carga una sola vez para ambos usos. Tiene tipo, destinatario del pago y monto, fijo o porcentaje del neto. El monto es positivo. Los costos no se borran: se anulan con motivo. El alcance real depende de si Big Media es dueña de los carteles o revende espacio de terceros (pregunta comercial pendiente).
- **Criterios de aceptación:**
  1. Dada una reserva, cuando el operativo agrega un costo, entonces queda asociado a ella.
  2. Dado un costo sin tipo, destinatario o monto, cuando se guarda, entonces se rechaza.
  3. Dado un costo anulado, cuando se calculan márgenes, entonces no se suma.

### HU-044 Ver el margen de una reserva

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero ver en cada reserva su ingreso total, costo total, margen y porcentaje de margen, para saber cuánto se ganó.
- **Prioridad:** Should
- **Complejidad:** S
- **Precondición:** HU-043 completa.
- **Regla de negocio:** Margen = total de la reserva menos costo total. El porcentaje es margen sobre ingreso; sin ingreso, no se calcula. Se muestra actualizado al momento de cargar un costo.
- **Criterios de aceptación:**
  1. Dada una reserva con ingreso 1000 y costos por 600, cuando se abre, entonces el margen es 400 y el porcentaje 40%.
  2. Dada una reserva sin ingreso, cuando se consulta, entonces no falla ni muestra un porcentaje inválido.
  3. Dada una reserva sin costos, cuando se consulta, entonces el margen es igual al ingreso.

### HU-045 Ver el margen de una campaña

- **Actor:** Gerencia
- **Descripción:** Como gerencia, quiero ver en la campaña la suma de ingresos, costos y margen de todas sus reservas, para evaluar su rentabilidad.
- **Prioridad:** Should
- **Complejidad:** S
- **Precondición:** HU-025 y HU-044 completas.
- **Regla de negocio:** Los agregados suman las reservas de la campaña, excluyendo las canceladas.
- **Criterios de aceptación:**
  1. Dada una campaña con varias reservas con costos, cuando se abre, entonces los totales coinciden con la suma manual.
  2. Dada una reserva cancelada, cuando se calcula, entonces no se suma.

### HU-046 Costo de alquiler a terceros

- **Actor:** Administrador
- **Descripción:** Como gerencia, quiero registrar el costo de alquiler cuando Big Media revende espacio de un tercero, para calcular el margen real por proveedor.
- **Prioridad:** Could
- **Complejidad:** L
- **Precondición:** Respuesta comercial de Gonzalo y Diego sobre si Big Media es dueña, revende o es mixta. Define si el módulo de costos son 20 o 60 horas.
- **Regla de negocio:** Si es mixta, se distingue a nivel cartel (tipo de propiedad y, si corresponde, tarifa de costo). Si es dueña, el alquiler no se carga como costo.
- **Criterios de aceptación:**
  1. Dado un cartel de tercero, cuando se reserva, entonces se puede cargar el costo de alquiler contra su proveedor.
  2. Dado un cartel propio, cuando se reserva, entonces el sistema no exige costo de alquiler.
  3. Dado el reporte de margen, cuando se filtra por proveedor, entonces muestra el costo de alquiler por tercero.

# E8 - Reportes y paneles

### HU-047 Panel principal

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero un panel de inicio con carteles libres y ocupados hoy, campañas activas y reservas por vencer, para ver el estado del negocio al entrar.
- **Prioridad:** Should
- **Complejidad:** M
- **Precondición:** HU-024 y HU-040 completas.
- **Regla de negocio:** Campaña activa es una Confirmada sin filtrar por fecha. "Por vencer" es una reserva confirmada cuya fecha de fin cae en los próximos 30 días (valor configurable).
- **Criterios de aceptación:**
  1. Dado el panel, cuando se abre, entonces muestra cantidad de carteles libres y ocupados, y de campañas activas.
  2. Dada una reserva por vencer, cuando se abre el panel, entonces aparece en la lista con acceso a su ficha.
  3. Dados los datos reales, cuando se abre el panel, entonces carga en menos de 3 segundos.

### HU-048 Reporte de ocupación

- **Actor:** Gerencia
- **Descripción:** Como gerencia, quiero ver el porcentaje de ocupación general y por cartel, para identificar los soportes de mejor rendimiento.
- **Prioridad:** Should
- **Complejidad:** L
- **Precondición:** HU-028 completa y datos reales cargados.
- **Regla de negocio:** La ocupación se mide en días-cupo: días-cupo ocupados sobre días-cupo disponibles, usando la capacidad real del cartel. Los séxtuples tienen capacidad variable y se tratan igual que los digitales, no como binarios. Por defecto se muestran separados por modalidad; nunca se promedian carteles fijos con LED.
- **Criterios de aceptación:**
  1. Dado un cartel fijo de capacidad 1 ocupado 15 de 30 días, cuando se mide, entonces su ocupación es 50%.
  2. Dado un LED de capacidad 20 con 10 cupos ocupados todo el mes, cuando se mide, entonces su ocupación es 50%.
  3. Dado el reporte, cuando se abre, entonces ofrece ranking de carteles, evolución mensual y mapa de calor cartel por mes, segmentable por modalidad y zona.

### HU-049 Reporte de ingresos por cliente y marca

- **Actor:** Gerencia
- **Descripción:** Como gerencia, quiero ver la facturación mensual y anual con desglose de agencia a marca, para saber quién genera más ingresos.
- **Prioridad:** Should
- **Complejidad:** M
- **Precondición:** HU-028 completa.
- **Regla de negocio:** El desglose sigue la cadena reserva, campaña, marca y cliente. El comparativo interanual aparece cuando haya historia suficiente. Los ingresos se reparten en el tiempo según HU-051.
- **Criterios de aceptación:**
  1. Dada una agencia, cuando se expande, entonces muestra sus marcas con sus ingresos.
  2. Dado el ranking de clientes y de marcas, cuando se ordena, entonces los totales cuadran contra la suma manual.
  3. Dado el reporte, cuando se filtra por período, entonces se ve facturación mensual y anual.

### HU-050 Análisis por rubro y grupo económico

- **Actor:** Gerencia
- **Descripción:** Como gerencia, quiero cortar ingresos y ocupación por rubro de la marca y por grupo económico, para saber qué industrias pautan más en vía pública.
- **Prioridad:** Could
- **Complejidad:** S
- **Precondición:** HU-017 completa. El grupo económico se toma de la marca (RN-016).
- **Regla de negocio:** El rubro se toma de la marca y no del cliente, que suele ser una agencia.
- **Criterios de aceptación:**
  1. Dada una campaña de una agencia para una marca de gastronomía, cuando se corta por rubro, entonces aparece Gastronomía y no Agencia de medios.
  2. Dado el corte por grupo económico, cuando se aplica, entonces suma las marcas del grupo.

### HU-051 Reparto de ingresos por día

- **Actor:** Sistema
- **Descripción:** Como gerencia, quiero que una reserva de varios meses reparta su ingreso proporcionalmente entre los meses en que corre, para que los reportes mensuales no queden distorsionados.
- **Prioridad:** Should
- **Complejidad:** M
- **Precondición:** HU-028 completa.
- **Regla de negocio:** El ingreso de una reserva se asigna a cada mes en proporción a los días que caen en él. Se reparte por días, lo que sirve tanto para alquileres mensuales como de 15 días. La suma de los meses siempre es igual al total de la reserva, resolviendo redondeos en el último tramo.
- **Criterios de aceptación:**
  1. Dada una reserva de septiembre a noviembre, cuando se mira el reporte mensual, entonces el ingreso se reparte en los tres meses proporcionalmente a sus días.
  2. Dada una reserva de 15 días, cuando se mide, entonces el ingreso se asigna por los días reales.
  3. Dada la suma de los meses, cuando se compara con el total de la reserva, entonces coincide al centavo.

### HU-052 Exportar reportes

- **Actor:** Gerencia
- **Descripción:** Como gerencia, quiero exportar cualquier reporte o lista filtrada a CSV o PDF, para compartirlo o trabajarlo fuera del sistema.
- **Prioridad:** Could
- **Complejidad:** M
- **Precondición:** HU-048 y HU-049 completas.
- **Regla de negocio:** La exportación respeta los filtros aplicados y los permisos del usuario. Los datos de facturación no se exportan a usuarios sin permiso.
- **Criterios de aceptación:**
  1. Dado un reporte filtrado, cuando se exporta a CSV, entonces el archivo contiene exactamente las filas visibles.
  2. Dado un usuario sin permiso de ver ingresos, cuando intenta exportar ese reporte, entonces se rechaza.
  3. Dado un reporte exportado a PDF, cuando se abre, entonces conserva el título, los filtros y la fecha de generación.

# E9 - Entrega y traspaso

### HU-053 Documentación técnica y traspaso del código

- **Actor:** Equipo de desarrollo
- **Descripción:** Como Big Media, quiero recibir el código fuente, la documentación técnica y las instrucciones de despliegue, para poder mantener y evolucionar el sistema con cualquier equipo.
- **Prioridad:** Must
- **Complejidad:** M
- **Precondición:** HU-002 completa y funcionalidad de las épicas E1 a E5 estable.
- **Regla de negocio:** Big Media se va a desvincular de MendoData a futuro, por lo que el sistema se construye con tecnologías estándar y abiertas, sin componentes que solo el proveedor pueda mantener. El código, la base de datos y los accesos son propiedad de Big Media.
- **Criterios de aceptación:**
  1. Dada la documentación, cuando la sigue una persona ajena al equipo original, entonces puede levantar el sistema en un entorno limpio.
  2. Dado el repositorio, cuando se revisa, entonces incluye modelo de datos, pruebas automatizadas y guía de contribución.
  3. Dada la entrega, cuando se cierra, entonces los accesos y credenciales quedan transferidos a Big Media.

### HU-054 Manual y capacitación

- **Actor:** Operativo
- **Descripción:** Como operativo, quiero un manual corto y una capacitación, para usar el sistema sin depender del equipo de desarrollo.
- **Prioridad:** Must
- **Complejidad:** S
- **Precondición:** E1 a E5 completas.
- **Regla de negocio:** La capacitación a Seba y Ale es presencial o grabada. Se hacen demos al cierre de cada etapa, porque las preguntas abiertas se responden mejor frente a una pantalla.
- **Criterios de aceptación:**
  1. Dado el manual, cuando lo sigue un operativo nuevo, entonces puede crear una campaña, reservar un cartel y entender un mensaje de conflicto.
  2. Dada la capacitación, cuando termina, entonces Seba y Ale la tienen disponible para consultarla.

# E10 - Armado de campañas y reserva masiva

### HU-055 Definir las posiciones solicitadas por formato

- **Actor:** Operativo
- **Descripción:** Como operador comercial, quiero agregar a la campaña líneas de formato con la cantidad de posiciones que necesito, para saber en todo momento cuánto me falta cubrir.
- **Prioridad:** Must
- **Complejidad:** S
- **Precondición:** HU-009 y HU-023 completas.
- **Regla de negocio:** Todas las líneas son opcionales y modificables después. Una línea sin cantidad es válida. No se puede repetir un formato en dos líneas de la misma campaña.
- **Criterios de aceptación:**
  1. Dada una campaña, cuando se agrega una línea con formato y cantidad, entonces queda guardada y visible en la campaña.
  2. Dada una línea con formato y sin cantidad, cuando se guarda, entonces se acepta.
  3. Dada una campaña con una línea de un formato, cuando se intenta agregar otra del mismo formato, entonces se rechaza con un mensaje claro.
  4. Dada una línea existente, cuando se cambia su cantidad o se quita, entonces las reservas ya creadas no se alteran.

### HU-056 Seleccionar carteles por formato con filtros

- **Actor:** Operativo
- **Descripción:** Como operador comercial, quiero abrir desde la campaña "Agregar carteles", elegir una línea de formato y ver solo los carteles de ese formato con cupo libre en el rango, para armar una tanda sin cargar reservas una por una.
- **Prioridad:** Must
- **Complejidad:** L
- **Precondición:** HU-014, HU-040 y HU-055 completas.
- **Regla de negocio:** La pantalla abre con la campaña precargada y bloqueada. Las fechas vienen de la campaña si las tiene; si no, la pantalla las pide para esa tanda y no se puede crear ninguna reserva sin ellas. Siempre se pueden ajustar para la tanda. Se filtra por zona, proveedor y dirección (búsqueda parcial, sin distinguir mayúsculas ni tildes). Cada cartel se identifica por Dirección + Tamaño (o Dirección + Slots en séxtuples), nunca por código interno. Seleccionar más o menos de lo solicitado genera un aviso, no un bloqueo. Queda fuera de alcance la autoselección ("completar hasta la cantidad") y la importación de la lista desde una planilla.
- **Criterios de aceptación:**
  1. Dada una línea de formato elegida, cuando se abre la lista, entonces solo muestra carteles de ese formato con cupo libre en el rango de fechas.
  2. Dada una campaña sin fechas, cuando se abre la pantalla, entonces pide fechas para la tanda y no permite continuar sin ellas.
  3. Dados filtros por zona, proveedor y dirección parcial, cuando se aplican, entonces la lista muestra solo los carteles que cumplen todos.
  4. Dada la lista filtrada, cuando el operativo usa "Seleccionar todos los filtrados" y destilda excepciones, entonces la selección refleja exactamente eso.
  5. Dada una selección, cuando cambia, entonces un contador muestra el avance por formato (por ejemplo "Gran Formato 60 de 100") y el monto estimado; si la línea no tiene cantidad, muestra solo lo seleccionado.
  6. Dada una selección mayor o menor a la solicitada, cuando se intenta confirmar, entonces el sistema avisa pero permite continuar.

### HU-057 Crear reservas en bloque

- **Actor:** Operativo
- **Descripción:** Como operador comercial, quiero que al confirmar la selección se cree una reserva por cada posición, para no cargar 100 o 200 reservas a mano.
- **Prioridad:** Must
- **Complejidad:** XL
- **Precondición:** HU-029, HU-030 y HU-056 completas.
- **Regla de negocio:** Cada reserva se crea en estado Pendiente con cartel, fecha de inicio y fecha de fin (obligatorios siempre) y el precio de alquiler tomado de la tarifa de lista, editable después. El nombre se autogenera ("Marca - Cartel - Mes"; "Sin marca" si la campaña aún no la tiene, y se corrige solo al cargarla). El operativo nunca carga número ni código de reserva. La operación debe ser idempotente: reintentar no duplica lo ya creado. Queda fuera de alcance la edición masiva de reservas ya creadas.
- **Criterios de aceptación:**
  1. Dada una selección de 200 posiciones, cuando se confirma, entonces se crean 200 reservas Pendientes en menos de 1 minuto (objetivo a validar), con progreso visible.
  2. Dada una reserva creada, cuando se abre, entonces tiene el precio de la tarifa de lista y un nombre autogenerado, sin que el operativo haya cargado nada más.
  3. Dada una tanda con fallos, cuando termina, entonces un resumen muestra cuántas se crearon y cuáles fallaron, con el motivo de cada una.
  4. Dadas las fallidas, cuando se reintentan, entonces solo se crean esas y no se duplican las ya creadas.
  5. Dada una falla del servidor a mitad de la tanda, cuando se vuelve a ejecutar, entonces el resultado final es el mismo que sin falla.

### HU-058 Seguimiento de lo solicitado, reservado y faltante

- **Actor:** Operativo
- **Descripción:** Como operador comercial, quiero ver en la campaña, por cada formato, cuántas posiciones solicité, cuántas reservé y cuántas faltan, para saber qué me queda por cubrir.
- **Prioridad:** Should
- **Complejidad:** M
- **Precondición:** HU-055 y HU-057 completas.
- **Regla de negocio:** Las reservas Canceladas no cuentan como reservadas. Si se cambian las fechas de la campaña y hay reservas Pendientes, el sistema pregunta si actualizarlas. Las reservas Confirmadas no se tocan sin pasar por la validación de solapamiento (HU-031).
- **Criterios de aceptación:**
  1. Dada una campaña con una línea de 100 posiciones y 60 reservas activas, cuando se abre, entonces muestra 100 solicitadas, 60 reservadas y 40 faltantes.
  2. Dada una línea sin cantidad, cuando se abre, entonces muestra solo las reservadas.
  3. Dado un cambio de fechas de la campaña con reservas Pendientes, cuando se guarda, entonces pregunta si se actualizan; si se acepta, se actualizan solo las Pendientes.
  4. Dado un cambio de fechas con reservas Confirmadas, cuando se guarda, entonces esas reservas no se modifican.

### HU-059 Confirmar la campaña y sus reservas en bloque

- **Actor:** Operativo
- **Descripción:** Como operador comercial, quiero confirmar la campaña y luego todas sus reservas pendientes de una vez, viendo los conflictos, para cerrar el armado de la campaña en un solo paso.
- **Prioridad:** Must
- **Complejidad:** L
- **Precondición:** HU-024, HU-031, HU-034 y HU-057 completas. Reemplaza a HU-026.
- **Regla de negocio:** Para pasar la campaña a Confirmada se exigen cliente que factura, marca y fechas; antes de eso, nada es obligatorio. Es una propuesta a validar con Seba: si quiere confirmar campañas incompletas, la exigencia se elimina y los reportes tendrán un grupo "(vacío)". "Confirmar reservas" valida el solapamiento de todas las pendientes juntas en el servidor, y lista los conflictos con cartel, fechas y la campaña que lo ocupa. Las reservas sin conflicto pasan a Confirmada; las conflictivas quedan Pendientes. Como la verificación de cupo es atómica por cartel (HU-034), el riesgo de que dos usuarios confirmen el mismo cartel a la vez queda cerrado, no solo reducido.
- **Criterios de aceptación:**
  1. Dada una campaña sin cliente, marca o fechas, cuando se pasa a Confirmada, entonces se rechaza indicando qué falta.
  2. Dada una campaña en estado Cotizada con datos incompletos, cuando se guarda, entonces se acepta.
  3. Dada una campaña con 200 reservas Pendientes, 190 sin conflicto y 10 con conflicto, cuando se usa "Confirmar reservas", entonces 190 pasan a Confirmada, 10 quedan Pendientes y se lista cada conflicto con cartel, fechas y campaña que lo ocupa.
  4. Dadas dos campañas que confirman a la vez el último cupo del mismo cartel, cuando se procesan, entonces una queda Confirmada y la otra Pendiente con su conflicto.
  5. Dados los conflictos ya resueltos, cuando se vuelve a usar "Confirmar reservas", entonces solo se procesan las que siguen Pendientes.
  6. Dado el recorrido completo, cuando el operador crea una campaña vacía, le agrega dos líneas de formato (100 y 100), reserva las 200 posiciones sin cargar ninguna a mano, completa cliente y marca y confirma las libres, entonces lo logra en menos de 5 minutos.

# E11 - Facturación mensual

### HU-060 Registrar un ítem a facturar

- **Actor:** Operativo
- **Descripción:** Como operador comercial, quiero cargar cada ítem a facturar en cualquier momento del mes, a medida que llega la orden de compra, para no armar la planilla a mano ni perder instrucciones de facturación.
- **Prioridad:** Must
- **Complejidad:** M
- **Precondición:** HU-016 y HU-017 completas.
- **Regla de negocio:** Ningún campo es obligatorio para guardar el ítem, igual que en la campaña; los datos se exigen recién al enviar a facturar (HU-066). Campos: mes de facturación (por defecto el mes actual, editable); cliente que factura y CUIT de facturación (precargado desde el cliente, editable por ítem); marca anunciante; descripción del servicio y período del servicio (desde y hasta); cantidad, precio unitario, importe neto y alícuota de IVA; tipo de servicio (alquiler, impresión y colocación, otro); tipo de soporte, Gob/Priv y tipo de venta (F/V); notas para Administración. El ítem puede vincularse opcionalmente a una campaña; esto es necesario porque "impresión y colocación" no es una reserva.
- **Criterios de aceptación:**
  1. Dado un ítem sin ningún dato, cuando se guarda, entonces se acepta.
  2. Dado un ítem nuevo, cuando se crea, entonces el mes de facturación es el mes actual y puede cambiarse.
  3. Dado un cliente elegido, cuando se carga, entonces el CUIT se precarga desde el cliente y puede editarse en el ítem sin modificar al cliente.
  4. Dado un ítem vinculado a una campaña, cuando se vincula, entonces cliente, marca y soporte se precargan desde ella.
  5. Dado un ítem sin campaña, cuando se carga, entonces todos sus datos se completan a mano.

### HU-061 Cálculo de importes e IVA

- **Actor:** Sistema
- **Descripción:** Como operador comercial, quiero que el importe neto, el IVA y el total se calculen solos, para no hacer cuentas a mano.
- **Prioridad:** Must
- **Complejidad:** S
- **Precondición:** HU-060 en construcción.
- **Regla de negocio:** El neto es cantidad por precio unitario, pero se puede sobrescribir, y también se puede cargar directamente como se hace hoy. El IVA y el total se calculan a partir del neto con la alícuota del ítem (la planilla actual solo muestra el neto). Los importes se redondean al centavo.
- **Criterios de aceptación:**
  1. Dada una cantidad 10 y un precio unitario 1000 con IVA 21%, cuando se guardan, entonces el neto es 10000, el IVA 2100 y el total 12100.
  2. Dado un neto sobrescrito a mano, cuando se guarda, entonces se respeta ese valor y el IVA y el total se recalculan desde él.
  3. Dado un ítem sin cantidad ni precio, cuando se carga solo el neto, entonces el IVA y el total se calculan igual.
  4. Dado un cambio de alícuota, cuando se guarda, entonces el IVA y el total se recalculan.

### HU-062 Orden de compra del ítem

- **Actor:** Operativo
- **Descripción:** Como operador comercial, quiero guardar en el ítem el número de orden de compra, su fecha de aprobación y el PDF, para respaldar lo que se factura.
- **Prioridad:** Should
- **Complejidad:** S
- **Precondición:** HU-060 completa.
- **Regla de negocio:** Por ahora la carga es manual, mirando el PDF; la lectura automática del PDF queda como mejora futura fuera de alcance. Si se carga un número de OC que ya existe, el sistema avisa de un posible duplicado, sin bloquear.
- **Criterios de aceptación:**
  1. Dado un ítem, cuando se carga número, fecha de aprobación y PDF, entonces quedan guardados y el PDF se puede abrir desde el ítem.
  2. Dado un número de OC ya existente en otro ítem, cuando se guarda, entonces el sistema avisa e indica el ítem coincidente, y permite guardar.
  3. Dado un archivo adjunto que no es PDF o supera el tamaño máximo, cuando se intenta adjuntar, entonces se rechaza con un mensaje claro.
  4. Dado un ítem sin orden de compra, cuando se guarda, entonces se acepta.

### HU-063 Costos del ítem y neto final

- **Actor:** Operativo
- **Descripción:** Como operador comercial, quiero cargar los costos incluidos en la factura de cada ítem y ver su costo total y neto final, para que Administración sepa qué costos tiene cada venta.
- **Prioridad:** Should
- **Complejidad:** M
- **Precondición:** HU-043, HU-060 y HU-061 completas.
- **Regla de negocio:** Cada ítem puede tener cero, uno o varios costos. Cada costo tiene tipo (comisión, proveedor, impresión), a quién se le paga y monto, que puede ser fijo o un porcentaje del neto (por ejemplo 15%). Son los mismos costos del módulo de costos y rentabilidad (HU-043): se cargan una sola vez y alimentan ambos usos. El ítem muestra costo total y neto final (importe neto menos costos). El total del mes se calcula solo y reemplaza las sumas manuales de la planilla actual (C15, D15 y C17).
- **Criterios de aceptación:**
  1. Dado un ítem con neto 10000 y un costo de 15% del neto, cuando se guarda, entonces el costo es 1500 y el neto final 8500.
  2. Dado un costo fijo, cuando se carga, entonces se resta tal cual del neto.
  3. Dado un cambio del neto, cuando se guarda, entonces los costos porcentuales se recalculan.
  4. Dado un ítem vinculado a una campaña, cuando se consulta la rentabilidad de la campaña, entonces cada costo se cuenta una sola vez, sin duplicarse.
  5. Dado un mes, cuando se consulta, entonces los totales de neto, costos y neto final coinciden con la suma manual de sus ítems.

### HU-064 Agrupar ítems en una factura y facturar a otro CUIT

- **Actor:** Operativo
- **Descripción:** Como operador comercial, quiero indicar que varios ítems van en una misma factura y poder facturar a un CUIT distinto del cliente, para transmitir esas instrucciones sin perderlas en las notas.
- **Prioridad:** Should
- **Complejidad:** S
- **Precondición:** HU-060 completa.
- **Regla de negocio:** Un ítem pertenece a un solo grupo de factura (por ejemplo "facturar todo en una FC con lo anterior"). La planilla de salida muestra los ítems agrupados. El CUIT de facturación del ítem puede ser distinto del CUIT del cliente.
- **Criterios de aceptación:**
  1. Dados tres ítems, cuando se agrupan, entonces comparten un mismo grupo de factura visible en cada uno.
  2. Dado un ítem agrupado, cuando se quita del grupo, entonces vuelve a ser independiente.
  3. Dada la planilla de salida, cuando se genera, entonces los ítems de un mismo grupo aparecen juntos y con el mismo identificador de grupo.
  4. Dado un ítem con CUIT distinto del cliente, cuando se guarda, entonces el cliente no cambia y la planilla muestra el CUIT del ítem.

### HU-065 Estados del ítem y número de factura

- **Actor:** Operativo
- **Descripción:** Como operador comercial, quiero que cada ítem tenga un estado (Borrador, Enviado a facturar o Facturado) y cargar el número de factura al facturarlo, para reemplazar el "ya facturado" escrito en texto.
- **Prioridad:** Must
- **Complejidad:** S
- **Precondición:** HU-060 completa.
- **Regla de negocio:** Los ítems nacen en Borrador. Al pasar a Facturado se exige el número de factura. Nunca se borra un ítem: se anula por estado, como el resto del sistema (HU-006). Quién pasa un ítem a Facturado (Seba o Administración) queda como pregunta abierta; mientras tanto lo hace el operativo.
- **Criterios de aceptación:**
  1. Dado un ítem nuevo, cuando se guarda, entonces queda en Borrador.
  2. Dado un ítem que pasa a Facturado, cuando se guarda sin número de factura, entonces se rechaza.
  3. Dado un ítem anulado, cuando se consultan totales y reportes, entonces no se suma, pero sigue visible en el histórico.
  4. Dado cualquier rol operativo, cuando mira un ítem, entonces no existe una acción de eliminar.

### HU-066 Cierre de mes y envío a Administración

- **Actor:** Operativo
- **Descripción:** Como operador comercial, quiero filtrar los ítems por mes y enviarlos todos a facturar con una planilla en el formato que conoce Administración, para no armar el listado a mano.
- **Prioridad:** Must
- **Complejidad:** L
- **Precondición:** HU-061, HU-063, HU-064 y HU-065 completas.
- **Regla de negocio:** La acción "Enviar a facturar" pasa los ítems del mes a Enviado a facturar y genera una planilla (.xlsx) con las mismas columnas que se usan hoy, más las nuevas: orden de compra, CUIT y grupo de factura. Al enviar se exigen cliente, importe neto y mes; antes de eso, nada es obligatorio (propuesta a validar con Seba, igual que en la campaña). Los ítems incompletos no se envían y se listan con lo que les falta; los completos sí (a validar con Seba). No se incluyen ítems anulados ni ya Facturados.
- **Criterios de aceptación:**
  1. Dado un mes elegido, cuando se filtra, entonces se ve el listado con total neto, costos y neto final.
  2. Dado un mes con ítems completos, cuando se usa "Enviar a facturar", entonces todos pasan a Enviado a facturar y se genera la planilla.
  3. Dada la planilla, cuando se abre, entonces tiene las columnas actuales de Administración más orden de compra, CUIT y grupo de factura, con los ítems agrupados.
  4. Dado un ítem sin cliente, sin importe neto o sin mes, cuando se intenta enviar, entonces no se envía y el sistema indica qué le falta.
  5. Dado un ítem anulado o ya Facturado, cuando se envía el mes, entonces no aparece en la planilla.
  6. Dado un envío realizado, cuando se consulta, entonces queda registrado quién lo hizo, cuándo y qué ítems incluyó.

### HU-067 Reabrir un ítem enviado

- **Actor:** Operativo
- **Descripción:** Como operador comercial, quiero poder reabrir un ítem ya enviado para corregirlo, dejando registro, y que Administración se entere del cambio, para que nadie facture con datos desactualizados.
- **Prioridad:** Should
- **Complejidad:** M
- **Precondición:** HU-007 y HU-066 completas.
- **Regla de negocio:** Un ítem Enviado a facturar no se edita sin una acción explícita de reabrir, que pide motivo y queda auditada (HU-007). Si algo cambia después del envío, Administración recibe un aviso con lo que cambió; el canal de aviso (por ejemplo correo) se define con ellos. Para ítems ya Facturados el comportamiento queda por definir.
- **Criterios de aceptación:**
  1. Dado un ítem Enviado a facturar, cuando se intenta editar sin reabrirlo, entonces el sistema lo impide.
  2. Dado un ítem Enviado, cuando se reabre, entonces se pide un motivo y queda registrado quién, cuándo y por qué.
  3. Dado un ítem reabierto, cuando se guardan cambios, entonces Administración recibe un aviso con los valores anteriores y nuevos.
  4. Dado un ítem reabierto y corregido, cuando se vuelve a enviar, entonces regresa a Enviado a facturar y queda marcado como reenviado.

# Supuestos y preguntas abiertas

Hay 12 decisiones del negocio que condicionan historias concretas. Hasta que se respondan, las historias afectadas llevan el default indicado.

| Tema | Historias afectadas | Quién responde | Default mientras tanto |
| --- | --- | --- | --- |
| Día de borde: ¿el 15 se pisa? | HU-001, HU-033 | Seba | Inclusivo (se pisa) |
| ¿La tentativa cuenta para el bloqueo duro? | HU-001, HU-033 | Seba | Ocupa cupo visual; bloqueo duro solo al confirmar |
| Estados físicos del cartel y qué hacer con reservas activas si se rompe | HU-012, HU-039 | Seba | Alertar y bloquear reservas nuevas |
| Listado de los 9 departamentos | HU-013 | Seba | Lista de zonas vacía y administrable |
| ¿Se puede confirmar una campaña incompleta, o se exigen cliente, marca y fechas al confirmar? | HU-059 | Seba | Se exigen cliente, marca y fechas (propuesta) |
| ¿Cambia el pagador de una marca, o una marca se compra por dos clientes? | HU-027 | Seba | Sin cliente propio en la campaña |
| ¿Big Media es dueña de los carteles o revende? | HU-043, HU-046 | Gonzalo y Diego | Costos solo de impresión y fijación |
| ¿Alcanza la vista de estado actual o hace falta ver a futuro? | HU-042 | Seba | Se construye como Should |
| ¿Administración usa el sistema o solo recibe la planilla? ¿Quién pasa un ítem a Facturado? | HU-065, HU-066, HU-067 | Seba y Administración | Administración recibe la planilla y los avisos por correo; Seba carga el número de factura |
| Alícuotas de IVA y valores de Gob/Priv y F/V | HU-060, HU-061 | Administración | Alícuota editable por ítem con 21% por defecto; Gob/Priv y F/V como listas administrables |
| Columnas exactas de la planilla actual de facturación | HU-066 | Seba | Se reproducen tal como están hoy; las nuevas van al final |
| ¿Qué distingue a un intermediario formal de uno común y qué datos lleva cada contacto? | HU-016, HU-068 | Seba | Tipo aparte; contacto con nombre, cargo, correo, teléfono y notas, y un contacto principal |

## Supuestos asumidos al escribir las historias

- **Relación Campaña, Marca y Cliente:** la campaña apunta a la marca anunciada y el cliente que factura se deduce de la marca. La alternativa era que la campaña tuviera dos vínculos propios (cliente y anunciante). Si se elige esa, cambian HU-023 y HU-027.
- **Tecnología libre:** las historias no fijan lenguaje, framework ni base de datos. La regla es que sean estándar y abiertas, y que el servidor sea la única autoridad sobre las validaciones de negocio, en particular la de solapamiento y la de concurrencia.
- **Doble reserva imposible:** a diferencia de una solución que valida en pantalla, acá HU-031 y HU-034 cierran el riesgo de condición de carrera de forma atómica en el servidor.
- **Estimaciones:** las complejidades son relativas y deben revisarse con el equipo antes de planificar iteraciones.
- **Otras preguntas aún abiertas** que no cambian el alcance pero sí detalles: capacidad uniforme de los LED, dimensiones estándar por formato, relevamiento de Banderolas, Mediano Formato, Monocolumnas y Carteleras, y quién además de Seba y Ale usará el sistema.

## Anexo: matriz de pruebas de disponibilidad (HU-031)

Casos que deben quedar cubiertos por pruebas automatizadas.

| Nº | Caso | Resultado esperado |
| --- | --- | --- |
| 1 | Rango idéntico a una reserva existente en cartel de capacidad 1 | Bloquea |
| 2 | Rango nuevo contenido dentro de uno existente | Bloquea |
| 3 | Rango nuevo que contiene a uno existente | Bloquea |
| 4 | Solapamiento parcial por izquierda | Bloquea |
| 5 | Solapamiento parcial por derecha | Bloquea |
| 6 | Rangos adyacentes (termina el 15, empieza el 15) | Según la configuración de día de borde |
| 7 | Rangos separados por un día | Permite |
| 8 | Conflicto con una reserva cancelada | Permite |
| 9 | Conflicto con una reserva tentativa | Según la configuración de tentativa |
| 10 | Cartel digital con 12 de 20 cupos ocupados | Permite |
| 11 | Cartel digital con 20 de 20 cupos ocupados | Bloquea |
| 12 | Edición que mueve las fechas a un rango ocupado | Bloquea |
| 13 | Edición que solo cambia el precio | No revalida |
| 14 | Edición que pasa la reserva a cancelada | Permite siempre |
| 15 | Dos confirmaciones simultáneas sobre el último cupo | Una pasa, una falla (HU-034) |
| 16 | Cartel en estado de baja, mantenimiento o apagado | Según HU-039 |
