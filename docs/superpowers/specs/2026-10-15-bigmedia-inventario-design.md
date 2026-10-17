# Big Media — diseño del módulo de inventario

Estado: para revisión de Juan Diego, 15 de octubre de 2026.

## Propósito y alcance

Esta entrega permite a Seba y Ale registrar y consultar los espacios publicitarios disponibles para vender. Es la base de datos operativa que luego usarán campañas y reservas. Cubre HU-008 a HU-014 de las historias de usuario, excepto las reglas que requieren reservas existentes. La importación CSV de HU-015 será una entrega posterior cuando estén disponibles las planillas tabulares.

La entrega incluye API y pantallas para proveedores, formatos, zonas y carteles. Los usuarios pueden crear, editar, inactivar y filtrar registros. No se cargan carteles ficticios. El estado inicial de las futuras campañas será **Borrador**; este módulo no crea campañas ni cotizaciones.

## Modelo de datos

- **Proveedor:** nombre único obligatorio, descripción del servicio opcional, activo/inactivo. Se conserva al inactivarlo.
- **Formato:** nombre único obligatorio, modalidad fija o digital, capacidad predeterminada entera mayor o igual a 1, dimensiones opcionales, activo/inactivo. Se crean PPL/Gran Formato, Banderolas, Séxtuples, LED, Mediano Formato, Monocolumnas y Carteleras; solo LED se marca digital inicialmente. La capacidad predeterminada de cada formato se deja en 1 como valor conservador y editable hasta confirmar los valores reales, especialmente para LED y séxtuples.
- **Zona:** nombre único obligatorio y activo/inactivo. La lista inicial, confirmada por Juan Diego a partir de la pantalla actual, contiene nueve departamentos: Ciudad, Godoy Cruz, Maipú, Luján de Cuyo, Guaymallén, Las Heras, San Martín, Rivadavia y San Carlos. «Todos» es una opción de filtro, no una zona guardada.
- **Estado físico:** catálogo administrable con Activo, En mantenimiento, De baja, Apagado y Vidrio destruido. Solo Activo será seleccionable en nuevas reservas cuando ese módulo exista. Se conserva todo estado histórico.
- **Cartel:** identificador interno, formato, dirección, zona, proveedor opcional, tamaño opcional, capacidad entera mayor o igual a 1, tarifa de lista no negativa, estado físico, enlace opcional de foto y fechas de creación/actualización. La capacidad se copia del formato al crear y después se puede editar sin alterar automáticamente un cartel existente. El nombre visible se compone de dirección y tamaño o cantidad de slots; el identificador interno no aparece como nombre comercial.

No se ofrece `DELETE` en la API ni en las pantallas. Las referencias históricas quedan intactas. Las restricciones de unicidad se aplican en PostgreSQL y los errores se devuelven con nombres de campo legibles.

## API y pantallas

La API Django REST Framework expondrá colecciones bajo `/api/inventario/` para proveedores, formatos, zonas, estados y carteles. Permitirá listar, consultar uno, crear y actualizar. Inactivar un catálogo o poner un cartel de baja se hará mediante actualización de estado. La lista de carteles aceptará filtros combinables por zona, formato, modalidad, estado y texto parcial de dirección; excluirá las bajas por defecto y ofrecerá incluirlas. El texto se comparará sin distinguir mayúsculas ni tildes.

React tendrá una sección **Carteles** con tabla, filtros y formulario de alta/edición. Mostrará nombre legible, formato, zona, proveedor, capacidad, tarifa y estado. Tendrá pantallas sencillas para administrar los catálogos. Al elegir un formato en un cartel nuevo, precargará su capacidad; el servidor repetirá esa regla para que también funcione por API. Las validaciones aparecen junto al campo afectado.

## Acceso y límites

El sistema usará usuarios y sesiones de Django. Las operaciones de inventario exigirán inicio de sesión; los cambios requerirán un usuario autorizado para operar. Esta primera entrega tendrá un rol operativo único mediante grupo de Django y un administrador. La política más detallada de HU-003 a HU-005 se especificará en la etapa de seguridad antes de poner el sistema en producción.

Como todavía no existen reservas, esta entrega no puede comprobar ocupación ni validar una reducción de capacidad contra reservas futuras. La modificación de capacidad se centralizará en un servicio para agregar esa validación y su auditoría al implementar reservas. La tarifa del cartel será solo el precio vigente de referencia; cada reserva futura guardará una copia del precio para preservar el histórico.

## Errores y pruebas

La API rechazará campos obligatorios ausentes, capacidad menor que 1, tarifa negativa, nombres duplicados y referencias a catálogos inactivos en carteles nuevos. Si falla una escritura, no quedará un registro parcial. Se probarán modelos, API autenticada, filtros combinados, búsqueda sin tildes, baja lógica y los formularios principales. Se ejecutarán migraciones y pruebas sobre PostgreSQL real, además de lint y compilación del frontend.

## Decisiones pendientes

Los valores reales de capacidad de LED y séxtuples y los estados físicos adicionales requieren confirmación de Big Media. No se inventarán carteles ni tarifas. La regla para reducir capacidad con reservas vigentes se cerrará junto con el motor de reservas. El tratamiento del día de borde entre reservas también se definirá antes de construir ese motor.
