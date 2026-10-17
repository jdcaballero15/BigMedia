# Importación del inventario de carteles

15 de octubre de 2026 · Historia principal: HU-015 · Relacionadas: HU-007, HU-009 a HU-013

Este documento define las plantillas CSV y las reglas de validación para cargar el inventario inicial. Por ahora cubre solo los dos formatos con relevamiento: **Gran Formato** (66 o más posiciones) y **Séxtuples** (226 posiciones). Banderolas, Mediano Formato, Monocolumnas y Carteleras no tienen relevamiento cuantitativo y no se importan hasta que lo tengan (HU-015). LED tampoco tiene relevamiento en las historias.

Las plantillas no traen filas de ejemplo con datos: no hay que inventar carteles. Los ejemplos de este documento usan valores marcados como ficticios.

## Archivos

| Archivo | Uso |
| --- | --- |
| [plantilla-gran-formato.csv](plantilla-gran-formato.csv) | Encabezado para el relevamiento de Gran Formato |
| [plantilla-sextuples.csv](plantilla-sextuples.csv) | Encabezado para el relevamiento de Séxtuples |
| [plantilla-reporte-importacion.csv](plantilla-reporte-importacion.csv) | Encabezado del reporte que devuelve cada importación |

## Requisitos previos

Antes de importar tienen que existir en el sistema:

1. **Los formatos** "PPL o Gran Formato" y "Séxtuples", activos, con su capacidad por defecto (HU-009).
2. **Las zonas.** La zona es obligatoria y la lista de departamentos todavía no está confirmada (decisión [D-08](../../reglas-de-negocio.md#rn-008-lista-de-zonas-departamentos-d-08)). Sin zonas no se puede importar ningún cartel.
3. **Los proveedores** que se nombren en el archivo (HU-008). El importador no crea proveedores nuevos, para que un error de tipeo no genere un proveedor duplicado.
4. **Los estados de cartel**, si el archivo trae la columna `estado` (HU-012).

Solo un usuario con rol Administrador puede importar (HU-015).

## Formato del archivo

- Codificación UTF-8. El importador rechaza el archivo si encuentra caracteres inválidos, para no guardar tildes rotas.
- Separador coma (`,`). Los valores que contengan comas van entre comillas dobles. Excel en español suele guardar con punto y coma: hay que exportar como "CSV UTF-8 (delimitado por comas)", o el importador puede detectar el `;` y avisarlo.
- La primera fila es el encabezado, con los nombres exactos de la plantilla. El orden de las columnas puede variar. Las columnas desconocidas hacen rechazar el archivo, para detectar errores de tipeo en el encabezado.
- Una fila por cartel. Sin celdas combinadas, subtotales, filas de título ni filas vacías intermedias.
- Los números van sin separador de miles. El decimal puede ser coma o punto.
- Un archivo contiene un solo formato.

### Cómo pasar la planilla visual a CSV

Las planillas actuales están en formato visual (HU-015). Para transformarlas:

1. Copiar cada posición a una fila de la plantilla, sin completar datos que la planilla no tenga.
2. Si un color, un resaltado o una celda combinada significa algo (estado, proveedor, cliente actual), pasarlo a la columna que corresponda o anotarlo en `ref_origen`. Preguntarle a Seba qué significa cada color antes de descartarlo (decisión [D-09](../../reglas-de-negocio.md#rn-009-contenido-real-de-los-relevamientos-d-09)).
3. Completar `ref_origen` con la hoja y la fila de origen (por ejemplo `GF hoja 1 fila 12`) para poder volver a la planilla cuando una fila se rechace.
4. Dejar vacío lo que no se sabe. Es mejor un cartel incompleto que un dato inventado.

## Columnas

### Gran Formato

| Columna | Obligatoria | Regla | Dónde se guarda |
| --- | --- | --- | --- |
| `formato` | Sí | Tiene que coincidir con el formato elegido al importar (por ejemplo, "PPL o Gran Formato") y estar activo | Cartel |
| `direccion` | Sí | Texto libre, de 3 a 200 caracteres | Cartel |
| `tamano` | Sí | Ancho x alto, por ejemplo `6x3` o `4,5x2`. Ver normalización | Cartel |
| `zona` | Sí | Debe existir en la lista de zonas, sin distinguir mayúsculas ni tildes | Cartel |
| `proveedor` | No | Si viene, debe existir y estar activo | Cartel |
| `tarifa_lista` | No | Número mayor o igual a 0, en pesos | Cartel |
| `estado` | No | Si viene, debe existir en la lista de estados. Vacío = Activo | Cartel |
| `foto_url` | No | Enlace `http` o `https` al almacenamiento externo (HU-010) | Cartel |
| `ref_origen` | No | Texto libre que identifica la fila en la planilla original | Solo en el reporte y la auditoría |
| `confirmar_distinto` | No | `si` o vacío. Ver duplicados | No se guarda |

La capacidad no va en el archivo: el cartel toma la capacidad por defecto del formato (HU-011).

### Séxtuples

Las mismas columnas, con `slots` en lugar de `tamano`:

| Columna | Obligatoria | Regla | Dónde se guarda |
| --- | --- | --- | --- |
| `slots` | Sí | Número entero mayor o igual a 1 | Capacidad del cartel (HU-015) |

En los séxtuples la cantidad de slots es a la vez la capacidad y parte de la identidad del cartel (HU-010). Cómo se trata un cambio de slots depende de la decisión [D-05](../../reglas-de-negocio.md#rn-005-slots-de-los-séxtuples-d-05).

## Normalización

Antes de validar, el importador normaliza cada valor sin perder el original:

- **Todos los campos.** Se quitan los espacios al principio y al final y se reducen los espacios repetidos a uno.
- **`tamano`.** Se pasa a minúsculas; `×` y `X` se convierten en `x`; se quitan los espacios y la unidad `m`; la coma decimal pasa a punto. `6 X 3`, `6x3 m` y `6×3` quedan como `6x3`. El resultado tiene que cumplir el patrón `número x número`. Si no, la fila se rechaza.
- **`slots`.** Tiene que ser un entero. `6,0` se acepta como 6; `6,5` se rechaza.
- **`zona`, `proveedor` y `estado`.** Se comparan con las listas del sistema sin distinguir mayúsculas ni tildes, y se guarda el nombre tal como está en la lista.
- **`direccion`.** Se guarda como viene, solo con los espacios limpios. Para comparar duplicados se usa una clave aparte (siguiente sección).

## Detección de duplicados

Big Media identifica un cartel por **Dirección + Tamaño** (Gran Formato) o **Dirección + Slots** (Séxtuples). No existe un código de cartel (HU-010). Por eso los duplicados se detectan con una clave construida a partir de esos datos.

### Clave exacta

`clave = formato + dirección normalizada + tamaño normalizado (o slots)`

La dirección normalizada:

1. Se pasa a minúsculas.
2. Se quitan las tildes (`á` → `a`, `ñ` se conserva).
3. Se quitan los signos `. , ; : # º °` y las comillas.
4. Se reducen los espacios repetidos.

Así, `Av. Ejemplo 123` y `av ejemplo  123` (direcciones ficticias) dan la misma clave.

### Clave aproximada (posible duplicado)

Señala casos que pueden ser el mismo cartel escrito distinto. No bloquea por sí sola: deja la fila en revisión.

1. **Abreviaturas.** Con la clave exacta se expanden abreviaturas comunes (`av` → `avenida`, `gral` → `general`, `bv` → `bulevar`, `esq` → `esquina`, `pje` → `pasaje`). La lista final de abreviaturas se arma con los relevamientos reales.
2. **Intersecciones en otro orden.** "Calle A y Calle B" contra "Calle B y Calle A": se ordenan las partes separadas por ` y ` o `esquina` antes de comparar.
3. **Errores de tipeo.** Dos direcciones del mismo formato con similitud alta (por ejemplo, distancia de edición de 1 o 2 caracteres) y el mismo tamaño o slots.
4. **Misma dirección, distinto tamaño o slots.** Puede ser otro cartel (otra cara) o un error. Pasa a revisión.
5. **Tamaño invertido.** `6x3` contra `3x6` en la misma dirección. Pasa a revisión hasta confirmar que el orden es siempre ancho x alto (decisión [D-09](../../reglas-de-negocio.md#rn-009-contenido-real-de-los-relevamientos-d-09)).

### Qué hace el importador en cada caso

| Situación | Resultado | Motivo |
| --- | --- | --- |
| La clave exacta ya existe en el sistema y los demás datos son iguales | `omitida` | Ya existe. Por eso importar dos veces el mismo archivo no duplica (HU-015, criterio 4) |
| La clave exacta ya existe en el sistema con algún dato distinto | `rechazada` | "Ya existe con datos distintos" y lista los campos. No se sobrescribe: los cambios se hacen desde la ficha del cartel |
| La clave exacta coincide con un cartel inactivo o de baja | `rechazada` | "Existe dado de baja". Se reactiva desde la ficha; no se crea otro |
| Dos filas del archivo con la misma clave exacta y datos iguales | La primera `creada`; las otras `rechazada` | "Fila repetida, igual a la fila N" |
| Dos filas del archivo con la misma clave exacta y datos distintos | Todas `rechazada` | "Conflicto entre las filas N y M". No se puede saber cuál es la correcta |
| Coincidencia aproximada con el sistema o con otra fila | `en_revision` | "Posible duplicado de …" con el nombre legible del cartel coincidente |
| Coincidencia aproximada y `confirmar_distinto = si` | `creada` | Se registra en el reporte que se confirmó a mano, como en HU-019 |

`confirmar_distinto` nunca habilita a cargar una fila con clave exacta repetida.

La comparación con el sistema incluye todos los carteles: activos, inactivos y de baja.

## Registros incompletos

Hay dos niveles:

- **Falta un dato obligatorio** (`formato`, `direccion`, `zona`, y `tamano` o `slots`): la fila se rechaza e indica cada campo faltante (HU-010, criterio 2).
- **Falta un dato opcional** (`proveedor`, `tarifa_lista`, `foto_url`): el cartel se crea y el reporte lo marca como incompleto, con la lista de campos vacíos. Sirve para completar después desde la ficha.

Un valor presente pero inválido (zona inexistente, tarifa negativa, enlace mal formado) siempre rechaza la fila, aunque el campo sea opcional. No se carga el cartel sin el dato, porque esconder el error haría que nadie lo corrija.

## Orden de validación

Para cada archivo:

1. **Archivo.** Codificación, separador, encabezado sin columnas faltantes ni desconocidas, al menos una fila de datos. Si falla, no se procesa ninguna fila.
2. **Fila por fila.**
   1. Normalización.
   2. Obligatorios.
   3. Tipos y rangos (tamaño, slots, tarifa, enlace).
   4. Referencias (formato, zona, proveedor, estado).
   5. Duplicados dentro del archivo.
   6. Duplicados contra el sistema.
3. **Carga.** Cada fila válida se guarda de forma independiente: una fila rechazada no impide cargar las demás (HU-015, criterio 3).

Se recomienda una **simulación** previa: el mismo proceso, sin guardar nada, que devuelve el reporte. Así se corrige el archivo antes de la carga real.

## Reporte de importación

Cada importación, simulada o real, devuelve un CSV con una fila por problema o por resultado ([plantilla](plantilla-reporte-importacion.csv)):

| Columna | Contenido |
| --- | --- |
| `fila` | Número de fila en el archivo, contando el encabezado como 1 |
| `ref_origen` | Lo que vino en esa columna |
| `resultado` | `creada`, `omitida`, `rechazada` o `en_revision` |
| `campo` | Campo afectado, si corresponde |
| `motivo` | Explicación en lenguaje claro, sin códigos internos |
| `cartel_coincidente` | Nombre legible del cartel con el que choca (Dirección + Tamaño o Slots) |

La pantalla de resultado muestra además un resumen: filas leídas, creadas, omitidas, rechazadas, en revisión y creadas incompletas.

Cada cartel creado queda auditado con el origen "importación", el nombre del archivo, el usuario y la fecha (HU-007).

## Pendientes que afectan la importación

| Decisión | Qué cambia en la importación |
| --- | --- |
| [D-05 Séxtuples](../../reglas-de-negocio.md#rn-005-slots-de-los-séxtuples-d-05) | Si los slots dejan de ser parte de la identidad, la clave pasa a ser solo la dirección |
| [D-07 Propiedad](../../reglas-de-negocio.md#rn-007-propiedad-de-los-carteles-d-07) | Podrían sumarse columnas de tipo de propiedad y tarifa de costo |
| [D-08 Zonas](../../reglas-de-negocio.md#rn-008-lista-de-zonas-departamentos-d-08) | Sin la lista no se puede importar |
| [D-09 Relevamientos](../../reglas-de-negocio.md#rn-009-contenido-real-de-los-relevamientos-d-09) | Formato del tamaño, significado de colores, abreviaturas reales, caras dobles |
| [D-10 Estados](../../reglas-de-negocio.md#rn-010-estados-físicos-y-carteles-fuera-de-servicio-preguntas-9-y-18-d-10) | Valores válidos de la columna `estado` |

## Fuera de alcance

- Actualizar carteles existentes desde un archivo. Por ahora los cambios se hacen desde la ficha.
- Importar formatos sin relevamiento, LED incluido.
- Importar reservas históricas (HU-038, con su propia plantilla cuando se defina la decisión D-12).
- Coordenadas geográficas: no figuran en las historias.
